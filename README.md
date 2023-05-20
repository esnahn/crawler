install python and git (I recommend using https://scoop.sh)

install VS code (or another editor)

run below in powershell

```powershell
scoop install versions/python311
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade --no-cache-dir pip
pip install -r .\requirements.txt

```

restart vs code

copy webdriver for selenium in the folder