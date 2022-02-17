Agents and Networks Model in Python
==============================

An implementation of the [GMU-Social Model](https://github.com/abmgis/abmgis/blob/master/Chapter08-Networks/Models/GMU-Social/README.md) in Python, using [Mesa](https://github.com/projectmesa/mesa) and [mesa-geo](https://github.com/Corvince/mesa-geo).

<p align="center">
  <img width="588" height="681" src="outputs/figures/ub_example.png">
</p>

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Run model

```python
python3 scripts/run.py --campus gmu
```

Change `gmu` to `ub` for a different campus map.
