if exist ".\venv" (

	call .\venv\Scripts\activate
	python -m ensurepip --upgrade
	python -m pip install --upgrade "pip>=22.3.1,<23.1.*"
	python -m pip install -r requirements.txt
	echo "DONE"
)