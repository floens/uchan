import esbuild from "esbuild";
import { sassPlugin } from "esbuild-sass-plugin";
import { writeFileSync } from "fs";
import * as path from "path";

const watchMode = process.argv.indexOf("--watch") >= 0;

const output = "build/static";
const metadataFile = "build/static/_meta.json";

const assets = [
  {
    entryPoint: "frontend/js/site.js",
    type: "script",
  },
  {
    entryPoint: "frontend/extra/extra.ts",
    type: "script",
  },
  {
    entryPoint: "frontend/style/style.sass",
    type: "style",
  },
  {
    entryPoint: "frontend/style/mod_style.sass",
    type: "mod_style",
  },
  {
    entryPoint: "frontend/style/extra.sass",
    type: "style",
  },
  {
    entryPoint: "frontend/style/themes/uchan.css",
    type: "theme",
  },
  {
    entryPoint: "frontend/style/themes/yotsuba.css",
    type: "theme",
  },
];

const saveMetadata = (result) => {
  if (!result) return;

  let metadata = {
    output: {},
  };

  for (let outputsKey in result.metafile.outputs) {
    let outputResult = result.metafile.outputs[outputsKey];
    let assetSpec = assets.find(
      (i) => i.entryPoint === outputResult.entryPoint
    );
    let name = path.basename(
      assetSpec.entryPoint,
      path.extname(assetSpec.entryPoint)
    );
    metadata.output[outputsKey] = {
      name: name,
      type: assetSpec.type,
    };
  }

  writeFileSync(metadataFile, JSON.stringify(metadata));
};

const context = await esbuild.context({
  entryPoints: assets.map((i) => i.entryPoint),
  outdir: output,
  metafile: true,
  bundle: true,
  minify: true,
  entryNames: "[name]-[hash]",
  target: "es6",
  plugins: [
    sassPlugin(),
    {
      name: "metadataSave",
      setup(build) {
        build.onEnd((result) => {
          saveMetadata(result);
          console.log("Build complete");
        });
      },
    },
  ],
});

if (watchMode) {
  console.log("Watch mode enabled");
  await context.watch();
} else {
  await context.rebuild();
  await context.dispose();
}
