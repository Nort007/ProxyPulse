# ProxyPulse

Fast and reliable proxy connectivity testing tool that supports multiple proxy protocol types.


![alt text](<Screenshot 2025-07-20 at 15.19.26.png>)

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