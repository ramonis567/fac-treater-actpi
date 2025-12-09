from pathlib import Path
import streamlit.web.bootstrap as bootstrap

def run():
    script_path = Path(__file__).parent / "main.py"

    bootstrap.run(
        main_script_path=str(script_path),
        is_hello=False,
        args=[],
        flag_options={}
    )


if __name__ == "__main__":
    run()
