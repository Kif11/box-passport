# Box Passport
BOX.com module that provide an robust way to login a user for your application.

Install module dependencies:
```bash
pip install -r requirements.txt
```

Create a configuration file `passport_config.json` inside the module directory with the following content:
```json
{
  "client_id": "your_clint_id",
  "client_secret": "your_client_secrec",
  "redirect_address": "http://127.0.0.1",
  "redirect_port": 8011
}
```
