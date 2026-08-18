import React from "react";
import { Composition } from "remotion";
import { loadFont } from "@remotion/google-fonts/Poppins";
loadFont("normal", { weights: ["400", "600", "700", "800", "900"] }); // load Poppins THẬT (trước đây fallback Arial) -> chữ sắc, chuẩn cho mọi kênh
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
loadAnton();  // Anton = condensed heavy display -> hook/số kiểu top data-channel USA (thay Poppins bo tròn generic)
import { LongBroke, calcLong } from "./LongBroke";
import { ShortGen, calcShortGen } from "./ShortGen";
import { GuessShort, calcGuess } from "./GuessShort";   // kênh #1 GUESS (đố/đoán)
import { BrandBroke } from "./BrandBroke";
import { Brand } from "./Brand";
import { BrandRanked } from "./BrandRanked";
import { StickDemo } from "./StickAnim";
import { StickStory, calcStory } from "./StickStory";
import { SayThisMG, calcMG } from "./SayThisMG";
import { BrandBeyond } from "./BrandBeyond";
import { BrandLegacy } from "./BrandLegacy";
import { Cinematic, calcCinematic } from "./Cinematic";
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
export const RemotionRoot: React.FC = () => (
  <>
    {/* LONG 16:9 & SHORT 9:16 — data-driven, đọc props.json (persona/giọng/palette theo kênh) */}
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
    <Composition id="CinematicShort" component={Cinematic} durationInFrames={300} fps={30} width={1080} height={1920} defaultProps={{ scenes: [], slug: "" }} calculateMetadata={calcCinematic} />
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
  </>
);
