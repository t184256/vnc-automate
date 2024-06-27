# vnc-automate

Programmatic interface for VNC.

Suitable for GUI testing over a VNC-connection.


This project is forked from [vnc-automate](https://github.com/univention/vnc-automate.git).
Some code from [univention-corporate-server](https://github.com/univention/univention-corporate-server/tree/5.2-0) has 
been integrated to make it easy usable for GUI testing with Pytest

# Build

```bash
apt-get install tesseract-ocr  # Optional language modules, such ss tesseract-ocr-deu, tesseract-ocr-nld

# Build a python package
python -m venv build
. bin/activate
pip install -r requirements.txt
python setup.py bdist_wheel
```

# Example with Pytest

This example for Pytest logs in and out on Windows over ssh-tunneled VNC


## Setup environment

Tessaract must be installed for OCR to work, don't forget to install extra language modules for any language except English.
The language used is passed as a parameter in the example below and must have a matching tesseract package installed. 

```bash
apt-get install tesseract-ocr  # Add optional language modules, such ss tesseract-ocr-deu

# Build a python package
python -m venv mytest
. bin/activate
pip install sshtunnel pytest
pip install '<build_dir>/dist/vnc_automate-2.0.0-cp311-cp311-linux_x86_64.whl'
```

For the example to work, the Windows machine under test must have SSH and VNC-server setup. The example expects to 
authenticate to SSH with the Windows credentials, the same as used to log in on the Windows desktop.
VNC-server on Windows shoeld NOT expect any authentication, which alright since it should just listen on localhost.

## Pytest example

```python
import os
from vncautomate.session import VNCSession, sleep, default_args
from vncautomate.helper import verbose
from sshtunnel import SSHTunnelForwarder
from yaml import safe_load


BASE_PATH = f'{os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))}'


def test_login_logoff():
    user = 'test_username'
    password = 'secret'
    windows_host = 'desktop.example.com'
    language = "eng"
    log_level = "info"

    output_path = f'{BASE_PATH}/log'
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # Debug:
    # os.environ['VNCAUTOMATE_TMP'] = "1"  # Keep-temp
    # os.environ['VNCAUTOMATE_DEBUG'] = "logging.yaml"  # Put logging.yml next to this file
    # Create args required by vnc-automate
    args = default_args(output_path, language=language, loglevel=log_level)
    # Add some args for our testcase:
    setattr(args, 'user', user)
    setattr(args, 'password', password)

    print(f'Windows host {windows_host}')
    server = SSHTunnelForwarder(windows_host, ssh_username=user, ssh_password=password,
                                remote_bind_address=('127.0.0.1', 5900))
    server.start()
    print(f"Ssh tunnel-port {server.local_bind_port}")  # show assigned local port
    setattr(args, 'vnc', f"localhost::{server.local_bind_port}")
    session = VNC(args=args)
    session.run()
    server.stop()

    
class VNC(VNCSession):
    def load_translation(self, language: str) -> dict[str, str]:
        name = os.path.join(os.path.dirname(__file__), "languages.yaml")
        if not os.path.exists(name):
            return {}
        with open(name) as fd:
            return {
                key: values.get(self.args.language, "")
                for key, values in safe_load(fd).items()
            }

    @verbose("MAIN")
    def main(self) -> None:
        print('Login flow') 
        self.login()
        print('Wait a little')
        sleep(10)
        print('logout flow')
        self.logout()

    @verbose("LOGIN")
    def login(self) -> None:
        self.client.keyPress("ctrl")
        if self.text_is_visible('OK', wait=False):
            self.client.keyPress("enter")
        self.click_on("User name")
        self.type(f"{self.args.user}\t{self.args.password}\n")
        # Login is completed when the Recycle Bin is visible
        self.wait_for_text('Recycle Bin')

    @verbose("LOGOUT")
    def logout(self) -> None:
        # self.client.<something> calls directly into vncdotool
        # vncdotool docs: https://vncdotool.readthedocs.io/en/latest/
        self.client.keyPress('super-r')
        self.wait_for_text('Run')
        self.type("logoff\n")
        sleep(3)
```

Save the python code e.g. as `test_windows.py` and run it with: `pytest -vs "test_windows.py"`

For multi-language support a `language.yaml` can be added, example:
```yaml
username:
  eng: "User name"
  deu: "Benuzter"
  nld: "Gebruikersnaam"
recycle_bin:
  eng: "Recycle Bin"
  deu: "Papierkorb"
  nld: "Prullenbak"
```

And install the language modules for OCR:
```bash
apt-get install tesseract-ocr-deu tesseract-ocr-nld
```

Change the language variable in the example and run it.


## Changes to the Univention vnc-automate code 

- Version increased to 2.0.0.
- Build and runtime dependencies updated.
- Code added from [univention-corporate-server](https://github.com/univention/univention-corporate-server/tree/5.2-0)
    - `test/utils/installation_test/helper.py` 
    - `test/utils/installation_test/installtion.py` as `session.py`
- In `client.py` the function `text_is_visible` with no wait fixed, so it returns after one OCR attempt.
- In `session.py` the class `VNCInstallation` is renamed to `VNCSession`.
- In `session.py` function `runner` returns to caller instead of exit
- In `session.py` a function `default_args` is added for easy args creations from a function.


# Original Univention documentation
## Docker image

Docker image with `vnc-automate` and [PyPI:`vncdotool`](https://pypi.org/project/vncdotool/) (univention/dist/vncdotool> is deprecated) based on `gitregistry.knut.univention.de/univention/dist/ucs-ec2-tools` from univention/dist/ucs-ec2-tools>.

## Pipeline

The pipeline builds the `vnc-automate` package from the source, creates the docker images and pushes the image to `gitregistry.knut.univention.de/univention/dist/vnc-automate` (for the main branch with the tag `latest`).

## Usage

See `ucs/test/utils/installation_test/installation.py` in univention/ucs>.

## Development

```sh
# create container, map current ucs-repo $HOME/git/ucs/test (for test utils) to /test
docker run --rm -it \
 -v "$HOME/ec2:$HOME/ec2:ro" \
 -v "$HOME/git/ucs/test:/test" \
 -w /test \
 --dns 192.168.0.124 \
 --dns 192.168.0.97 \
 --dns-search knut.univention.de \
 gitregistry.knut.univention.de/univention/dist/vnc-automate \
 bash

# now in the container, start an installation on a pre-defined machine
python utils/installation_test/vnc-install-ucs.py --vnc isala:2 --language deu --role basesystem --fqdn base
```

## Testing

```
mkdir dump/
VNCAUTOMATE_DEBUG=logging.yaml \
VNCAUTOMATE_TMP=1 \
python3 -m vncautomate.cli \
	--log debug \
	--dump-boxes dump/boxes.png \
	--dump-dir dump/ \
	--dump-screen dump/screen.png \
	--dump-x-gradients dump/x.png \
	--dump-y-gradients dump/y.png \
	--lang eng tests/login.png Username
```
