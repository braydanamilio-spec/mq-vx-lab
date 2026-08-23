#!/usr/bin/env python3
"""BẾN PHỤ CLOUDFLARE R2 (23/8/2026) — chỗ đậu tạm khi MỌI kho Drive từ chối.

Vì sao có file này: sáng 23/8, 180 video render xong bị Drive từ chối (lỗi scope) và chỉ còn nằm
trong artifact GitHub — hết hạn là mất. R2 cho 10GB free/tài khoản, dùng chung nhà Cloudflare đã có
sẵn nên không phải mở dịch vụ mới. Video đẩy hụt Drive sẽ nằm ở R2, phiên sau tự chuyển về Drive.

R2 KHÔNG thay Drive. Nó chỉ là bến tạm: Drive sống lại -> chuyển về -> xoá khỏi R2 để trả chỗ.

Khoá lưu chung hồ key (collection gemini_keys) theo dạng CHUỖI 1 DÒNG:
    r2:<account_id>:<access_key_id>:<secret_access_key>:<bucket>
Nhiều tài khoản = nhiều dòng; hệ tự xoay vòng, dòng nào đầy/hỏng thì sang dòng kế.
"""
import os
import time

_CACHE = {"at": 0.0, "pool": []}


def parse_key(raw: str) -> dict | None:
    """'r2:acc:akid:secret:bucket' -> dict. Sai định dạng -> None (bỏ qua, không làm chết luồng)."""
    s = str(raw or "").strip()
    if not s.lower().startswith("r2:"):
        return None
    p = s[3:].split(":")
    if len(p) < 4:
        return None
    acc, akid, secret, bucket = p[0].strip(), p[1].strip(), p[2].strip(), ":".join(p[3:]).strip()
    if not (acc and akid and secret and bucket):
        return None
    return {"account": acc, "akid": akid, "secret": secret, "bucket": bucket,
            "endpoint": f"https://{acc}.r2.cloudflarestorage.com"}


def pool(keys: list[dict] | None = None) -> list[dict]:
    """Danh sách tài khoản R2: lấy từ hồ key (dòng r2:...) + env R2_KEYS (ngăn bằng dấu phẩy)."""
    if _CACHE["pool"] and (time.time() - _CACHE["at"]) < 300:
        return _CACHE["pool"]
    out = []
    for raw in (os.environ.get("R2_KEYS", "") or "").split(","):
        k = parse_key(raw)
        if k:
            out.append(k)
    for k in (keys or []):
        p = parse_key(k.get("key") if isinstance(k, dict) else k)
        if p:
            p["id"] = k.get("id") if isinstance(k, dict) else None
            out.append(p)
    # bỏ trùng theo (account, bucket)
    seen, uniq = set(), []
    for p in out:
        sig = (p["account"], p["bucket"])
        if sig not in seen:
            seen.add(sig)
            uniq.append(p)
    _CACHE["at"], _CACHE["pool"] = time.time(), uniq
    return uniq


def _client(acc: dict):
    import boto3                                     # chỉ nạp khi thật sự dùng R2
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=acc["endpoint"],
                        aws_access_key_id=acc["akid"], aws_secret_access_key=acc["secret"],
                        config=Config(signature_version="s3v4", retries={"max_attempts": 2}),
                        region_name="auto")


def used_bytes(acc: dict) -> int:
    """Đang chiếm bao nhiêu byte trong bucket này (để chọn tài khoản còn chỗ)."""
    try:
        cl = _client(acc)
        tot, tok = 0, None
        while True:
            kw = {"Bucket": acc["bucket"], "MaxKeys": 1000}
            if tok:
                kw["ContinuationToken"] = tok
            r = cl.list_objects_v2(**kw)
            tot += sum(int(o.get("Size", 0)) for o in r.get("Contents", []) or [])
            if not r.get("IsTruncated"):
                return tot
            tok = r.get("NextContinuationToken")
    except Exception:
        return 0


CAP_BYTES = 9 * 1024 ** 3          # chừa ~1GB dưới mức 10GB free


def upload(path: str, name: str, keys: list[dict] | None = None) -> dict | None:
    """Đẩy 1 file lên tài khoản R2 còn chỗ. Trả {account,bucket,key,size} hoặc None nếu không đường nào được."""
    accs = pool(keys)
    if not accs:
        print("   ℹ️ R2: chưa có khoá nào (thêm dòng r2:... ở tab key) — bỏ qua bến phụ.")
        return None
    size = os.path.getsize(path)
    for acc in accs:
        try:
            if used_bytes(acc) + size > CAP_BYTES:
                print(f"   ⏭ R2 {acc['account'][:8]}…/{acc['bucket']} gần đầy -> thử tài khoản khác")
                continue
            _client(acc).upload_file(path, acc["bucket"], name)
            print(f"   🅿️ R2: đã gửi tạm {name} ({size/1e6:.1f}MB) vào {acc['bucket']}")
            return {"account": acc["account"], "bucket": acc["bucket"], "key": name, "size": size}
        except Exception as e:
            print(f"   ⚠️ R2 {acc['bucket']} lỗi ({str(e)[:70]}) -> thử tài khoản khác")
    return None


def download(meta: dict, dest: str, keys: list[dict] | None = None) -> str | None:
    """Tải file từ R2 về máy để đẩy sang Drive."""
    for acc in pool(keys):
        if acc["account"] != meta.get("account") or acc["bucket"] != meta.get("bucket"):
            continue
        try:
            _client(acc).download_file(acc["bucket"], meta["key"], dest)
            return dest
        except Exception as e:
            print(f"   ⚠️ R2 tải về lỗi ({str(e)[:70]})")
    return None


def delete(meta: dict, keys: list[dict] | None = None) -> bool:
    """Xoá khỏi R2 sau khi đã chuyển về Drive — trả lại chỗ cho lượt sau."""
    for acc in pool(keys):
        if acc["account"] != meta.get("account") or acc["bucket"] != meta.get("bucket"):
            continue
        try:
            _client(acc).delete_object(Bucket=acc["bucket"], Key=meta["key"])
            return True
        except Exception:
            return False
    return False


def status(keys: list[dict] | None = None) -> list[dict]:
    """Báo cáo dung lượng từng tài khoản R2 (cho dashboard/log)."""
    out = []
    for acc in pool(keys):
        u = used_bytes(acc)
        out.append({"account": acc["account"][:8] + "…", "bucket": acc["bucket"],
                    "used_gb": round(u / 1024 ** 3, 2), "free_gb": round(max(0, CAP_BYTES - u) / 1024 ** 3, 2)})
    return out
