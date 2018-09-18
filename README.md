### Install locally

```shell
pip install .
```

### Make executable with PyInstaller

```shell
pyinstaller -F \
  --name shyr \
  --distpath ~/Desktop \
  --specpath /tmp \
  cli.py
```
