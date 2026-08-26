import React from "react";
import { Composition } from "remotion";
import { loadFont } from "@remotion/google-fonts/Poppins";
loadFont("normal", { weights: ["400", "600", "700", "800", "900"] }); // load Poppins THẬT (trước đây fallback Arial) -> chữ sắc, chuẩn cho mọi kênh
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
loadAnton();  // Anton = condensed heavy display -> hook/số kiểu top data-channel USA (thay Poppins bo tròn generic)
import { LongBroke, calcLong } from "./LongBroke";
import { ShortGen, calcShortGen } from "./ShortGen";
import { GuessShort, calcGuess } from "./GuessShort";   // kênh #1 GUESS (đố/đoán)
import { BrandGuess } from "./BrandGuess";              // brand kênh #1 GUESS
import { MappedShort, calcMapped } from "./MappedShort"; // kênh #2 MAPPED (choropleth US)
import { BrandMapped } from "./BrandMapped";             // brand kênh #2 MAPPED
import { RankedShort, calcRanked } from "./RankedShort";  // kênh #3 RANKED (tier list)
import { BrandRanked2 } from "./BrandRanked2";            // brand kênh #3 RANKED
import { ScaledShort, calcScaled } from "./ScaledShort";  // kênh #4 SCALED (so sánh kích thước)
import { SwarmShort, calcSwarm } from "./SwarmShort";  // kênh #7 SWARM (mật độ đám đông, hạt bay lấp đầy)
import { BrandSwarm } from "./BrandSwarm";
import { PulseShort, calcPulse } from "./PulseShort";  // kênh #8 PULSE (cường độ giác quan, gauge kim)
import { BrandPulse } from "./BrandPulse";
import { ClockworkShort, calcClockwork } from "./ClockworkShort";  // kênh #9 CLOCKWORK (nén thời gian)
import { BrandClockwork } from "./BrandClockwork";
import { LongshotShort, calcLongshot } from "./LongshotShort";  // kênh #10 LONGSHOT (xác suất thật)
import { BrandLongshot } from "./BrandLongshot";
import { BrandScaled } from "./BrandScaled";             // brand kênh #4 SCALED
import { ThenNowShort, calcThenNow } from "./ThenNowShort"; // kênh #5 THEN×NOW (xưa/nay)
import { BrandThenNow } from "./BrandThenNow";           // brand kênh #5 THEN×NOW
import { BrandDoc } from "./BrandDoc";                   // brand PARAMETRIC Wave 2 (Cosmos/Deep/Why/Empire/Unsolved)
import { BrandBroke } from "./BrandBroke";
import { Brand } from "./Brand";
import { BrandRanked } from "./BrandRanked";
import { StickDemo } from "./StickAnim";
import { StickStory, calcStory } from "./StickStory";
import { SayThisMG, calcMG } from "./SayThisMG";
import { BrandBeyond } from "./BrandBeyond";
import { BrandLegacy } from "./BrandLegacy";
import { Cinematic, calcCinematic } from "./Cinematic";
import { ToonShort, calcToon } from "./ToonShort";
import { DocThumb } from "./DocThumb";
import { DoChu } from "./DoChu";
import { BarChartRace, calcRace } from "./BarChartRace";
import { BrandV2 } from "./BrandV2";
import { WorldMapRace } from "./WorldMapRace";
import { BrandRace } from "./BrandRace";
import { RaceLong, calcMulti } from "./RaceLong";
import { LottieTest } from "./LottieTest";
import { Thumb, calcThumb } from "./Thumb";
import { LongV2, calcV2 } from "./LongV2";
import { GenDemo } from "./GenDemo";
import { ConceptDemo } from "./Concepts";
import { LottiePrev } from "./LottiePrev";

// 🎬 ENGINE MM0 — chỉ giữ composition ACTIVE (long/short data-driven + brand). Sạch, gọn.
// Cỡ chuẩn từng nền tảng — xem BRAND_KIT.md mục 2. Thêm nền tảng = thêm một dòng ở đây.
const CO_BRAND: Record<string, [number, number]> = {
  banner: [2560, 1440],      // YouTube cover
  avatar: [800, 800],        // YouTube avatar
  watermark: [150, 150],     // watermark video, nền trong suốt
  fb_cover: [1640, 624],     // Facebook cover
  fb_avatar: [500, 500],     // Facebook avatar
  ig_avatar: [640, 640],     // Instagram avatar
  ig_story: [1080, 1920],    // Instagram highlight cover
};
const calcBrandKit2 = ({ props }: any) => {
  const [w, h] = CO_BRAND[String(props?.kind || "banner")] || CO_BRAND.banner;
  return { width: w, height: h, durationInFrames: 1, fps: 30 };
};

export const RemotionRoot: React.FC = () => (
  <>
    {/* LONG 16:9 & SHORT 9:16 — data-driven, đọc props.json (persona/giọng/palette theo kênh) */}
    {/* 25/8 — MỘT composition cho CẢ 7 asset brand-kit thế hệ 2. Trước đây mỗi cỡ phải khai một
        Composition riêng (banner/avatar/watermark…), thêm nền tảng là thêm 3 dòng; `remotion still`
        lại không cho ghi đè kích thước từ dòng lệnh. Đọc cỡ từ props qua calculateMetadata thì
        thêm cỡ mới chỉ là thêm một dòng trong bảng CO_BRAND. */}
    <Composition id="BrandKit2" component={BrandV2} durationInFrames={1} fps={30}
      width={2560} height={1440} defaultProps={{ kind: "banner" }} calculateMetadata={calcBrandKit2} />
    <Composition id="BrandV2Banner" component={BrandV2} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandV2Avatar" component={BrandV2} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="RaceBanner" component={BrandRace} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="RaceAvatar" component={BrandRace} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="RaceWatermark" component={BrandRace} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="RaceLong" component={RaceLong} durationInFrames={300} fps={30} width={1920} height={1080} defaultProps={{ races: [] }} calculateMetadata={calcMulti} />
    <Composition id="RaceLongV" component={RaceLong} durationInFrames={300} fps={30} width={1080} height={1920} defaultProps={{ races: [] }} calculateMetadata={calcMulti} />
    <Composition id="Race" component={BarChartRace} durationInFrames={300} fps={30} width={1920} height={1080} defaultProps={{ frames: [{ t: 2000, data: [{ name: "A", value: 1 }] }] }} calculateMetadata={calcRace} />
    <Composition id="WorldRace" component={WorldMapRace} durationInFrames={300} fps={30} width={1920} height={1080} defaultProps={{ frames: [{ t: 2000, data: [{ name: "China", value: 1 }] }] }} calculateMetadata={calcRace} />
    <Composition id="RaceShort" component={BarChartRace} durationInFrames={300} fps={30} width={1080} height={1920} defaultProps={{ frames: [{ t: 2000, data: [{ name: "A", value: 1 }] }] }} calculateMetadata={calcRace} />
    <Composition id="LongBroke" component={LongBroke} durationInFrames={5425} fps={30} width={1920} height={1080} defaultProps={{ scenes: [], slug: "broke_long" }} calculateMetadata={calcLong} />
    <Composition id="ShortGen" component={ShortGen} durationInFrames={600} fps={30} width={1080} height={1920} defaultProps={{ scenes: [], slug: "" }} calculateMetadata={calcShortGen} />
    <Composition id="GuessShort" component={GuessShort} durationInFrames={660} fps={30} width={1080} height={1920} calculateMetadata={calcGuess}
      defaultProps={{ title: "GUESS THE US CITY", handle: "@guessusa", color: "#F5B301", accent: "#ff375f", roundSec: 7, rounds: [
        { q: "Guess this US city", clue: "8.3M people · Wall Street", answer: "NEW YORK CITY", stat: "Rent: $3,900/mo 😳" },
        { q: "Which US city is this?", clue: "Hollywood · 4M people", answer: "LOS ANGELES", stat: "Avg home: $970K" },
        { q: "Name this skyline", clue: "Windy City · Lake Michigan", answer: "CHICAGO", stat: "3rd biggest US metro" },
      ] }} />
    <Composition id="LongV2" component={LongV2} durationInFrames={600} fps={30} width={1920} height={1080} defaultProps={{ scenes: [], slug: "" }} calculateMetadata={calcV2} />
    {/* BRAND kênh #1 GUESS */}
    <Composition id="BrandGuessAvatar" component={BrandGuess} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandGuessBanner" component={BrandGuess} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandGuessWatermark" component={BrandGuess} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="GuessThumb" component={BrandGuess} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    {/* KÊNH #2 MAPPED — choropleth US states */}
    <Composition id="MappedShort" component={MappedShort} durationInFrames={330} fps={30} width={1080} height={1920} calculateMetadata={calcMapped}
      defaultProps={{ title: "HIGHEST INCOME BY STATE", unit: "median household income", color: "#22D3EE", accent: "#22D3EE", handle: "@mappedusa", topN: 3, data: [
        { state: "Maryland", value: 98461, disp: "$98,461" }, { state: "Massachusetts", value: 96505, disp: "$96,505" },
        { state: "New Jersey", value: 97126, disp: "$97,126" }, { state: "California", value: 91905, disp: "$91,905" },
        { state: "New York", value: 81386, disp: "$81,386" }, { state: "Texas", value: 73035, disp: "$73,035" },
        { state: "Florida", value: 67917, disp: "$67,917" }, { state: "Mississippi", value: 52719, disp: "$52,719" },
        { state: "West Virginia", value: 55217, disp: "$55,217" }, { state: "Alabama", value: 59609, disp: "$59,609" },
        { state: "Washington", value: 90325, disp: "$90,325" }, { state: "Colorado", value: 87598, disp: "$87,598" },
        { state: "Virginia", value: 87249, disp: "$87,249" }, { state: "Illinois", value: 78433, disp: "$78,433" },
        { state: "Ohio", value: 66990, disp: "$66,990" }, { state: "Georgia", value: 71355, disp: "$71,355" },
        { state: "Arizona", value: 72581, disp: "$72,581" }, { state: "Oregon", value: 76362, disp: "$76,362" },
      ] }} />
    {/* BRAND kênh #2 MAPPED */}
    <Composition id="BrandMappedAvatar" component={BrandMapped} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandMappedBanner" component={BrandMapped} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandMappedWatermark" component={BrandMapped} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="MappedThumb" component={BrandMapped} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    {/* KÊNH #3 RANKED — tier list */}
    <Composition id="RankedShort" component={RankedShort} durationInFrames={360} fps={30} width={1080} height={1920} calculateMetadata={calcRanked}
      defaultProps={{ title: "FAST FOOD, RANKED", subtitle: "by US sales", color: "#7C5CFF", accent: "#7C5CFF", handle: "@rankedusa", tiers: ["S", "A", "B", "C", "D"], items: [
        { name: "McDonald's", tier: "S", stat: "$53B" }, { name: "Starbucks", tier: "S", stat: "$31B" },
        { name: "Chick-fil-A", tier: "A", stat: "$21B" }, { name: "Taco Bell", tier: "A", stat: "$15B" },
        { name: "Wendy's", tier: "B", stat: "$12B" }, { name: "Dunkin'", tier: "B", stat: "$11B" },
        { name: "Subway", tier: "C", stat: "$10B" }, { name: "Domino's", tier: "C", stat: "$9B" },
        { name: "Arby's", tier: "D", stat: "$5B" },
      ] }} />
    {/* BRAND kênh #3 RANKED */}
    <Composition id="BrandRanked2Avatar" component={BrandRanked2} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandRanked2Banner" component={BrandRanked2} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandRanked2Watermark" component={BrandRanked2} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="RankedThumb" component={BrandRanked2} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    {/* KÊNH #4 SCALED — so sánh kích thước */}
    <Composition id="ScaledShort" component={ScaledShort} durationInFrames={360} fps={30} width={1080} height={1920} calculateMetadata={calcScaled}
      defaultProps={{ title: "HOW BIG IS A BLUE WHALE?", subtitle: "length compared", color: "#2FA84F", accent: "#2FA84F", handle: "@scaledusa", items: [
        { name: "Human", emoji: "🧍", value: 1.7, disp: "1.7 m" },
        { name: "Great White", emoji: "🦈", value: 6, disp: "6 m" },
        { name: "School Bus", emoji: "🚌", value: 12, disp: "12 m" },
        { name: "Blue Whale", emoji: "🐋", value: 30, disp: "30 m" },
      ] }} />
    {/* BRAND kênh #4 SCALED */}
    <Composition id="BrandScaledAvatar" component={BrandScaled} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandScaledBanner" component={BrandScaled} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandScaledWatermark" component={BrandScaled} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="ScaledThumb" component={BrandScaled} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    {/* KÊNH #5 THEN×NOW — split xưa/nay */}
    <Composition id="ThenNowShort" component={ThenNowShort} durationInFrames={450} fps={30} width={1080} height={1920} calculateMetadata={calcThenNow}
      defaultProps={{ title: "GAS PRICES: THEN vs NOW", color: "#EC4899", accent: "#EC4899", handle: "@thennowusa", pairs: [
        { label: "Gallon of Gas", thenYear: "1970", thenVal: "$0.36", nowYear: "2024", nowVal: "$3.50", change: "×10" },
        { label: "Movie Ticket", thenYear: "1970", thenVal: "$1.55", nowYear: "2024", nowVal: "$11.50", change: "×7" },
        { label: "New House", thenYear: "1970", thenVal: "$23K", nowYear: "2024", nowVal: "$420K", change: "×18" },
      ] }} />
    {/* BRAND kênh #5 THEN×NOW */}
    <Composition id="BrandThenNowAvatar" component={BrandThenNow} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandThenNowBanner" component={BrandThenNow} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandThenNowWatermark" component={BrandThenNow} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="ThenNowThumb" component={BrandThenNow} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    {/* WAVE 2 — 5 brand tài liệu (parametric BrandDoc) */}
    {[
      { id: "Cosmos", name: "COSMOS", emoji: "🌌", accent: "#7C5CFF", accent2: "#22D3EE", handle: "@cosmosdaily", tagline: "The universe, explained." },
      { id: "Deep", name: "THE DEEP", emoji: "🌊", accent: "#0EA5E9", accent2: "#22D3EE", handle: "@thedeepdaily", tagline: "The ocean's darkest secrets." },
      { id: "Why", name: "WHY", emoji: "🔬", accent: "#F59E0B", accent2: "#F5B301", handle: "@whydaily", tagline: "Why everything is the way it is." },
      { id: "Empire", name: "EMPIRE", emoji: "👑", accent: "#EAB308", accent2: "#F5B301", handle: "@empiredaily", tagline: "How they built it all." },
      { id: "Unsolved", name: "UNSOLVED", emoji: "🌍", accent: "#EF4444", accent2: "#F59E0B", handle: "@unsolveddaily", tagline: "Mysteries with no answer." },
      // WAVE 8 (21/8) — 10 kênh mới, cùng khuôn parametric (màu/handle khớp brands.json)
      { id: "Made", name: "MADE USA", emoji: "🏭", accent: "#E76F51", accent2: "#FFD166", handle: "@madeusa", tagline: "How America makes it." },
      { id: "Built", name: "BUILT USA", emoji: "🏗️", accent: "#457B9D", accent2: "#F4A261", handle: "@builtusa", tagline: "Engineering, at American scale." },
      { id: "Under", name: "UNDER USA", emoji: "🕳️", accent: "#5E548E", accent2: "#E0AAFF", handle: "@underusa", tagline: "America, underneath." },
      { id: "Relic", name: "RELIC USA", emoji: "🏚️", accent: "#8D6A4F", accent2: "#D9C5A0", handle: "@relicusa", tagline: "What America left behind." },
      { id: "First", name: "FIRST USA", emoji: "🥇", accent: "#B22234", accent2: "#FFFFFF", handle: "@firstusa", tagline: "The moment it began." },
      { id: "Branded", name: "BRANDED USA", emoji: "🔖", accent: "#111827", accent2: "#F43F5E", handle: "@brandedusa", tagline: "The story behind the logo." },
      { id: "Priced", name: "PRICED USA", emoji: "🧾", accent: "#0F766E", accent2: "#FDE047", handle: "@pricedusa", tagline: "Where your dollar goes." },
      { id: "Haul", name: "HAUL USA", emoji: "🚛", accent: "#CA8A04", accent2: "#1D4ED8", handle: "@haulusa", tagline: "America in motion." },
      { id: "Fake", name: "FAKE USA", emoji: "🕵️", accent: "#DC2626", accent2: "#0EA5A5", handle: "@fakeusa", tagline: "Spot the fake." },
      { id: "Farm", name: "FARM USA", emoji: "🌾", accent: "#65A30D", accent2: "#FBBF24", handle: "@farmusa", tagline: "From soil to shelf." },
    ].flatMap((b) => ([
      <Composition key={b.id + "A"} id={`BrandDoc${b.id}Avatar`} component={BrandDoc} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar", name: b.name, emoji: b.emoji, accent: b.accent, accent2: b.accent2, handle: b.handle, tagline: b.tagline }} />,
      <Composition key={b.id + "B"} id={`BrandDoc${b.id}Banner`} component={BrandDoc} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner", name: b.name, emoji: b.emoji, accent: b.accent, accent2: b.accent2, handle: b.handle, tagline: b.tagline }} />,
      <Composition key={b.id + "W"} id={`BrandDoc${b.id}Watermark`} component={BrandDoc} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark", name: b.name, emoji: b.emoji, accent: b.accent, accent2: b.accent2 }} />,
      <Composition key={b.id + "T"} id={`Doc${b.id}Thumb`} component={BrandDoc} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb", name: b.name, emoji: b.emoji, accent: b.accent, accent2: b.accent2, handle: b.handle }} />,
    ]))}

    {/* THUMBNAIL data-driven (mỗi video 1 thumb, đọc props) */}
    <Composition id="Thumb" component={Thumb} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ bigLine: "SO HIGH?!", topLine: "WHY IS RENT" }} calculateMetadata={calcThumb} />
    {/* THUMBNAIL & BRAND */}
    <Composition id="BrokeThumb" component={BrandBroke} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    <Composition id="BrandBrokeAvatar" component={BrandBroke} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandBrokeBanner" component={BrandBroke} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandInsideAvatar" component={Brand} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ ch: "inside", kind: "avatar" }} />
    <Composition id="BrandInsideBanner" component={Brand} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ ch: "inside", kind: "banner" }} />
    <Composition id="BrandHuhAvatar" component={Brand} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ ch: "huh", kind: "avatar" }} />
    <Composition id="BrandHuhBanner" component={Brand} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ ch: "huh", kind: "banner" }} />
    <Composition id="BrandRankedAvatar" component={BrandRanked} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandRankedBanner" component={BrandRanked} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandBeyondAvatar" component={BrandBeyond} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandBeyondBanner" component={BrandBeyond} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandLegacyAvatar" component={BrandLegacy} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandLegacyBanner" component={BrandLegacy} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandLegacyWatermark" component={BrandLegacy} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="Cinematic" component={Cinematic} durationInFrames={300} fps={30} width={1920} height={1080} defaultProps={{ scenes: [], slug: "" }} calculateMetadata={calcCinematic} />
    <Composition id="DoChu" component={DoChu} durationInFrames={1} fps={30} width={2400} height={300} defaultProps={{ text: "ABCDEFGHIJ", font: "poppins" }} />
    <Composition id="DocThumb" component={DocThumb} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ big: "TITLE" }} />
    <Composition id="CinematicShort" component={Cinematic} durationInFrames={300} fps={30} width={1080} height={1920} defaultProps={{ scenes: [], slug: "" }} calculateMetadata={calcCinematic} />
    <Composition id="ToonShort" component={ToonShort} durationInFrames={300} fps={30} width={1080} height={1920} defaultProps={{ slug: "", title: "", frames: [], lines: [] }} calculateMetadata={calcToon} />
    <Composition id="ToonLong" component={ToonShort} durationInFrames={300} fps={30} width={1920} height={1080} defaultProps={{ slug: "", title: "", frames: [], lines: [] }} calculateMetadata={calcToon} />
    <Composition id="LottieTest" component={LottieTest} durationInFrames={120} fps={30} width={1920} height={1080} />
    <Composition id="StickDemo" component={StickDemo} durationInFrames={230} fps={30} width={1080} height={1920} />
    <Composition id="StickStory" component={StickStory} durationInFrames={880} fps={30} width={1080} height={1920} calculateMetadata={calcStory} />
    <Composition id="SayThisMG" component={SayThisMG} durationInFrames={900} fps={30} width={1080} height={1920} defaultProps={{ scenes: [] }} calculateMetadata={calcMG} />
    <Composition id="SayThisMGWide" component={SayThisMG} durationInFrames={900} fps={30} width={1920} height={1080} defaultProps={{ scenes: [] }} calculateMetadata={calcMG} />
    <Composition id="StickStoryWide" component={StickStory} durationInFrames={880} fps={30} width={1920} height={1080} calculateMetadata={calcStory} />
    <Composition id="GenDemo" component={GenDemo} durationInFrames={120} fps={30} width={1920} height={1080} defaultProps={{ arch: "office", seed: 1, channel: "broke", nar: "" }} />
    <Composition id="GenDemoV" component={GenDemo} durationInFrames={120} fps={30} width={1080} height={1920} defaultProps={{ arch: "office", seed: 1, channel: "broke", nar: "" }} />
    <Composition id="ConceptDemo" component={ConceptDemo} durationInFrames={90} fps={30} width={1920} height={1080} defaultProps={{ name: "subscriptions", caption: "" }} />
    <Composition id="LottiePrev" component={LottiePrev} durationInFrames={90} fps={30} width={1080} height={1080} defaultProps={{ file: "a.json" }} />
      <Composition id="SwarmShort" component={SwarmShort} durationInFrames={360} fps={30} width={1080} height={1920} calculateMetadata={calcSwarm} />
    <Composition id="BrandSwarmAvatar" component={BrandSwarm} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandSwarmBanner" component={BrandSwarm} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandSwarmWatermark" component={BrandSwarm} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="SwarmThumb" component={BrandSwarm} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    <Composition id="PulseShort" component={PulseShort} durationInFrames={360} fps={30} width={1080} height={1920} calculateMetadata={calcPulse} />
    <Composition id="BrandPulseAvatar" component={BrandPulse} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandPulseBanner" component={BrandPulse} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandPulseWatermark" component={BrandPulse} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="PulseThumb" component={BrandPulse} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    <Composition id="ClockworkShort" component={ClockworkShort} durationInFrames={360} fps={30} width={1080} height={1920} calculateMetadata={calcClockwork} />
    <Composition id="BrandClockworkAvatar" component={BrandClockwork} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandClockworkBanner" component={BrandClockwork} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandClockworkWatermark" component={BrandClockwork} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="ClockworkThumb" component={BrandClockwork} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
    <Composition id="LongshotShort" component={LongshotShort} durationInFrames={360} fps={30} width={1080} height={1920} calculateMetadata={calcLongshot} />
    <Composition id="BrandLongshotAvatar" component={BrandLongshot} durationInFrames={1} fps={30} width={800} height={800} defaultProps={{ kind: "avatar" }} />
    <Composition id="BrandLongshotBanner" component={BrandLongshot} durationInFrames={1} fps={30} width={2560} height={1440} defaultProps={{ kind: "banner" }} />
    <Composition id="BrandLongshotWatermark" component={BrandLongshot} durationInFrames={1} fps={30} width={150} height={150} defaultProps={{ kind: "watermark" }} />
    <Composition id="LongshotThumb" component={BrandLongshot} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ kind: "thumb" }} />
  </>
);