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
import { BrandScaled } from "./BrandScaled";             // brand kênh #4 SCALED
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
