:: Create virtual environment, activate it, and install python requirements
python -m venv .venv
call .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

:: Run npm script to build react-vite app & generate static bundle
cd frontend_gui 
call npm install
call npm run build

:: Return to original directory
cd ..

:: At the end of this script, you will no longer be in the virtual environment. 
:: To get back in, run '.\.venv\Scripts\activate' from the command line
