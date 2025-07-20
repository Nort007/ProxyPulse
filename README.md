# ProxyPulse

Fast and reliable proxy connectivity testing tool that supports multiple proxy protocol types.

<img width="998" height="192" alt="Screenshot 2025-07-20 at 15 19 26" src="https://github.com/user-attachments/assets/06a25392-dd64-4dde-8ecf-afe08b2c44be" />

## How to run

### Installation

<pre>
# cp Pipfile.dist Pipfile
# pipenv install
</pre>

### Usage

<pre>
# pipenv run python3 proxy_pulse.py -p 1.2.3.4:1234:login:secret_password
</pre>


### Options
- <code>'--file'</code> (<code>--file proxies.txt</code>) - option allows to specify file .txt with proxies
- <code>--proxies</code> (<code>--proxies 1.2.3.4:1234:login:password</code>) - option allows to specify proxies via space-separated
- <code>'--url'</code> (<code>--url https://example.com/ip</code>) - option allows to specify url destination
- <code>'--debug'</code> - option allows see action in debug mode
