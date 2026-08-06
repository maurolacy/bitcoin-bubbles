(* Helper: export a dated prediction plot under predictions/ and refresh the -latest copy.
   Requires `base` (notebook directory, with trailing slash) to be set.
   Load with: Get[base <> "PredictionsExport.wl"]

   Note: `-latest.png` is a regular file copy (not a symlink). GitHub's README
   renderer does not reliably follow symlinks for images. *)

ClearAll[exportPrediction];

exportPrediction[plot_, nameStem_String, date_String] := Module[
  {dir, datedName, latestName, datedPath, latestPath},
  (* `base` is DirectoryName[NotebookFileName[]] and usually has a trailing slash *)
  dir = base <> "predictions";
  CreateDirectory[dir, CreateIntermediateDirectories -> True];
  datedName = nameStem <> "-" <> date <> ".png";
  latestName = nameStem <> "-latest.png";
  datedPath = FileNameJoin[{dir, datedName}];
  latestPath = FileNameJoin[{dir, latestName}];
  Export[datedPath, plot];
  (* Plain copy so GitHub can serve the image from the fixed README path *)
  If[FileExistsQ[latestPath] || DirectoryQ[latestPath], DeleteFile[latestPath]];
  CopyFile[datedPath, latestPath];
  {datedPath, latestPath}
];

(* Examples (after plots are built):
exportPrediction[pricePlot, "BTC_PricePrediction", lastPriceDate]
exportPrediction[pricePlot, "Gold(PAXG)_PricePrediction", lastPriceDate]
exportPrediction[pricePlot, "Silver(KAG)_PricePrediction", lastPriceDate]
exportPrediction[bitcoinOvervaluation, "BTC_Overvaluation-P", last]
exportPrediction[bitcoinOvervaluationNp, "BTC_Overvaluation-NP", last]
*)
