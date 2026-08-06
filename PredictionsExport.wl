(* Helper: export a dated prediction plot under predictions/ and refresh the -latest symlink.
   Requires `base` (notebook directory, with trailing slash) to be set.
   Load with: Get[base <> "PredictionsExport.wl"] *)

ClearAll[exportPrediction];

exportPrediction[plot_, nameStem_String, date_String] := Module[
  {dir, datedName, latestName, datedPath, latestPath, linkResult},
  (* `base` is DirectoryName[NotebookFileName[]] and usually has a trailing slash *)
  dir = base <> "predictions";
  CreateDirectory[dir, CreateIntermediateDirectories -> True];
  datedName = nameStem <> "-" <> date <> ".png";
  latestName = nameStem <> "-latest.png";
  datedPath = FileNameJoin[{dir, datedName}];
  latestPath = FileNameJoin[{dir, latestName}];
  Export[datedPath, plot];
  (* Relative symlink via ln: CreateSymbolicLink often fails when the target is a
     basename (resolved against $HomeDirectory / cwd, not the link's directory). *)
  linkResult = RunProcess[
    {"ln", "-sfn", datedName, latestName},
    ProcessDirectory -> dir
  ];
  If[linkResult["ExitCode"] =!= 0,
    Message[exportPrediction::linkfail, latestName, linkResult["StandardError"]];
    Return[$Failed]
  ];
  {datedPath, latestPath}
];

exportPrediction::linkfail = "Failed to create symlink `1`: `2`";

(* Examples (after plots are built):
exportPrediction[pricePlot, "BTC_PricePrediction", lastPriceDate]
exportPrediction[pricePlot, "Gold(PAXG)_PricePrediction", lastPriceDate]
exportPrediction[pricePlot, "Silver(KAG)_PricePrediction", lastPriceDate]
exportPrediction[bitcoinOvervaluation, "BTC_Overvaluation-P", last]
exportPrediction[bitcoinOvervaluationNp, "BTC_Overvaluation-NP", last]
*)
