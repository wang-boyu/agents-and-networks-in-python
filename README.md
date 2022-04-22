Agents and Networks Model in Python
==============================

<p align="center">
  <img width="588" height="681" src="outputs/figures/ub_example.png">
</p>

## Introduction

This is an implementation of the [GMU-Social Model](https://github.com/abmgis/abmgis/blob/master/Chapter08-Networks/Models/GMU-Social/README.md) in Python, using [Mesa](https://github.com/projectmesa/mesa) and [mesa-geo](https://github.com/Corvince/mesa-geo).

## How it works

Campus maps are loaded from shapefiles (.shp) in the `data/raw` directory, defining buildings for commuters to live and work, and roads for commuters to move around the campus. During model setup, every commuter is randomly assigned a building as home and another building as work place. Shortest path between home and work locations are computed using the A-star algorithm.

## How to use it

### Install

```bash
python3 -m pip install -r requirements.txt
```

### Run model

```python
python3 scripts/run.py --campus ub
```

Change `ub` to `gmu` for a different campus map.

## License

MIT
