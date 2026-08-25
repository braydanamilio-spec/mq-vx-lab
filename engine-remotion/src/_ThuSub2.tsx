import React from "react";
import { AbsoluteFill } from "remotion";
const doSang=(hex:string):number=>{const h=String(hex||"").replace("#","");
  const v=h.length===3?h.split("").map(c=>c+c).join(""):h;
  const r=parseInt(v.slice(0,2),16)/255,g=parseInt(v.slice(2,4),16)/255,b=parseInt(v.slice(4,6),16)/255;
  if([r,g,b].some(x=>Number.isNaN(x)))return .5; return .2126*r+.7152*g+.0722*b;};
const TU=["By","1890","the","script","moved","onto"], A=4;
const Cu:React.FC<{ac:string}>=({ac})=>(
  <div style={{position:"absolute",left:0,right:0,bottom:30,textAlign:"center",padding:"0 40px",textShadow:"0 2px 18px rgba(0,0,0,.95)"}}>
    {TU.map((x,i)=>{const on=i===A;return <span key={i} style={{fontSize:46,fontWeight:900,color:on?ac:"#EAF8FF",margin:"0 9px",display:"inline-block"}}>{x}</span>;})}
  </div>);
const Moi:React.FC<{ac:string}>=({ac})=>(
  <div style={{position:"absolute",left:0,right:0,bottom:30,textAlign:"center",padding:"0 40px"}}>
    <div style={{display:"inline-block",background:"rgba(8,10,16,0.46)",borderRadius:20,padding:"8px 20px",lineHeight:1.35}}>
      {TU.map((x,i)=>{const on=i===A;return <span key={i} style={{fontSize:46,fontWeight:900,display:"inline-block",
        margin:on?"0 6px":"0 11px",padding:on?"0 10px":0,borderRadius:on?12:0,background:on?ac:"transparent",
        color:on?(doSang(ac)>0.55?"#12131A":"#FFFFFF"):"#F4FAFF",
        boxShadow:on?"0 0 0 4px rgba(255,255,255,0.92), 0 4px 18px rgba(0,0,0,0.55)":"none",
        WebkitTextStroke:on?"0px":"7px rgba(8,10,16,0.92)",paintOrder:"stroke fill"} as React.CSSProperties}>{x}</span>;})}
    </div>
  </div>);
const CA=[{n:"nền ĐỎ RỰC · accent navy",bg:"#E01B24",ac:"#2C3E50"},
          {n:"nền trời SÁNG · accent nhạt",bg:"linear-gradient(180deg,#1E88E5,#E3F2FD)",ac:"#7FC8F8"},
          {n:"nền TỐI · accent vàng",bg:"linear-gradient(180deg,#0B1020,#12203A)",ac:"#F5B301"}];
export const ThuSub2:React.FC=()=>(
  <AbsoluteFill style={{fontFamily:"Poppins,Arial"}}>
    {CA.map((c,k)=>(
      <div key={k} style={{position:"absolute",left:0,right:0,top:`${k*33.34}%`,height:"33.34%",background:c.bg,overflow:"hidden"}}>
        <div style={{position:"absolute",top:10,left:20,fontSize:20,fontWeight:800,color:"#fff"}}>{c.n}</div>
        <div style={{position:"absolute",left:0,width:"50%",top:0,bottom:0}}>
          <div style={{position:"absolute",top:40,left:20,fontSize:18,fontWeight:800,color:"#fff"}}>CŨ</div><Cu ac={c.ac}/></div>
        <div style={{position:"absolute",right:0,width:"50%",top:0,bottom:0}}>
          <div style={{position:"absolute",top:40,left:20,fontSize:18,fontWeight:800,color:"#fff"}}>MỚI</div><Moi ac={c.ac}/></div>
      </div>))}
  </AbsoluteFill>);
