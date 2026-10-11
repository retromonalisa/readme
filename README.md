<!--
  Art lives in ./assets as plain SVG (no third-party widgets or trackers).
  To change it, edit assets/src/*.py and run:
    python3 assets/src/banner.py assets && python3 assets/src/pipeline.py assets
-->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
    <img src="assets/banner-light.svg" width="100%" alt="retromonalisa: teaching cameras to watch the sky. Pixel-art camera view with a small drone boxed and labelled 'drone 0.73'.">
  </picture>
</p>

## 👋 Hi, I'm retromonalisa

I like computer vision that has to hold up outside the lab. Right now that means teaching a camera to spot drones against open sky, with the model running **on the image sensor itself**, and checking the results in real outdoor field tests.

## 🛰️ Currently building

### [seraphim-sky](https://github.com/retromonalisa/seraphim-sky)

Drone detection with the detector running on the camera's image sensor itself.

<p>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/pipeline-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/pipeline-light.svg">
    <img src="assets/pipeline-light.svg" width="100%" alt="seraphim-sky pipeline: a dataset of 83k images, train the detector, deploy it on the sensor, field test outdoors.">
  </picture>
</p>

- **Data:** built on an 83k-image drone detection dataset
- **Train → deploy:** a documented pipeline from training to running on the sensor, plus a quick start
- **Field-tested:** a real drone over an open field, against a cloudy sky
- **License:** MIT

Related repo: [`imx500_seraphim_sky`](https://github.com/retromonalisa/imx500_seraphim_sky)

## 🧭 What I'm into

- 👁️ **Computer vision:** object detection, from dataset to deployed model
- 📟 **Edge AI:** models small enough to run on the device, or right on the sensor
- 🌤️ **Field testing:** real skies, real clouds, real drones

<br>

<p align="center"><sub>✦ thanks for stopping by ✦</sub></p>
