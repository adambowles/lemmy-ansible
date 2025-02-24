import os
import pathlib
import shutil
import sys

# Dependencies
from InquirerPy import inquirer
import yaml

# sed a file. See: https://stackoverflow.com/a/13089373
def replace_text_in_file(filename, replacements):
    lines = []
    with open(filename) as infile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            lines.append(line)
    with open(filename, 'w') as outfile:
        for line in lines:
            outfile.write(line)

# Clean up previous run
if os.path.exists('inventory') or os.path.exists('templates/pictrs.yml'):
    cleanup = inquirer.confirm(message='Clean up previous run').execute()

    if cleanup:
        if os.path.exists('inventory'):
            shutil.rmtree('inventory')
        if os.path.exists('templates/pictrs.yml'):
            os.remove('templates/pictrs.yml')
            shutil.copyfile('examples/pictrs.yml', 'templates/pictrs.yml')
    else:
        print('A clean run is recommended! Be sure to inspect the output files if you choose not to perform a clean run')
else:
    shutil.copyfile('examples/pictrs.yml', 'templates/pictrs.yml')

domain = inquirer.text(
    message='Domain to deploy',
    default='example.com',
).execute()

if not domain:
    print('Domain required')
    sys.exit(0)

if not os.path.exists('inventory/host_vars/' + domain):
    pathlib.Path('inventory/host_vars/' + domain).mkdir(parents=True, exist_ok=True)

configFileSrc = 'examples/config.hjson'
configFileDest = 'inventory/host_vars/' + domain + '/config.hjson'

if not os.path.exists(configFileDest):
    pathlib.Path(configFileDest)
    shutil.copyfile(configFileSrc, configFileDest)
    
postgresqlFileSrc = 'examples/customPostgresql.conf'
postgresqlFileDest = 'inventory/host_vars/' + domain + '/customPostgresql.conf'

if not os.path.exists(postgresqlFileDest):
    pathlib.Path(postgresqlFileDest)
    shutil.copyfile(postgresqlFileSrc, postgresqlFileDest)

hostsFileSrc = 'examples/hosts'
hostsFileDest = 'inventory/hosts'

if os.path.exists(hostsFileDest):
    os.remove(hostsFileDest)

pathlib.Path(hostsFileDest)
shutil.copyfile(hostsFileSrc, hostsFileDest)

user = inquirer.text(
    message='User on your domain',
    default='root',
    long_instruction = 'User you use to connect to your server via ssh'
).execute()
letsencrypt_contact_email = inquirer.text(
    message = 'Let\'s Encrypt contact email', 
    default = 'admin@' + domain,
    long_instruction = 'Your email address to get notifications if your ssl cert expires'
).execute()
lemmy_base_dir = inquirer.text(
    message='Lemmy base directory',
    default='/srv/lemmy',
    long_instruction = 'The location on the server where lemmy can be installed, can be any folder. If you are upgrading from a previous version, set this to `/lemmy`'
).execute()

replacements = {
    'myuser@example.com  domain=example.com  letsencrypt_contact_email=your@email.com  lemmy_base_dir=/srv/lemmy': user + '@' + domain + '  domain=' + domain + '  letsencrypt_contact_email=' + letsencrypt_contact_email + '  lemmy_base_dir=/srv/lemmy',
}
replace_text_in_file(hostsFileDest, replacements)

object_storage = inquirer.confirm(
    message='Use object storage',
    instruction = 'Object storage (e.g. AWS S3) may reduce operating costs (y/N)'
).execute()

if object_storage:
    PICTRS__STORE__ENDPOINT = inquirer.text(
        message = 'Object store endpoint',
    ).execute()
    PICTRS__STORE__BUCKET_NAME = inquirer.text(
        message = 'Object store bucket name',
    ).execute()
    PICTRS__STORE__REGION = inquirer.text(
        message = 'Object store region',
    ).execute()
    PICTRS__STORE__USE_PATH_STYLE = inquirer.confirm(
        message = 'Object store use path style',
    ).execute()
    PICTRS__STORE__ACCESS_KEY = inquirer.text(
        message = 'Object store access key',
    ).execute()
    PICTRS__STORE__SECRET_KEY = inquirer.text(
        message = 'Object store secret key',
    ).execute()

    with open('templates/pictrs.yml', 'r') as file:
        pictrs = yaml.safe_load(file)

    # Add object store keys
    pictrs['pictrs_env_vars'] = [
        'PICTRS__STORE__TYPE=object_storage',
        'PICTRS__STORE__ENDPOINT=' + PICTRS__STORE__ENDPOINT,
        'PICTRS__STORE__BUCKET_NAME=' + PICTRS__STORE__BUCKET_NAME,
        'PICTRS__STORE__REGION=' + PICTRS__STORE__REGION,
        'PICTRS__STORE__USE_PATH_STYLE=' + str(PICTRS__STORE__USE_PATH_STYLE).lower(),
        'PICTRS__STORE__ACCESS_KEY=' + PICTRS__STORE__ACCESS_KEY,
        'PICTRS__STORE__SECRET_KEY=' + PICTRS__STORE__SECRET_KEY,
    ]

    with open('templates/pictrs.yml', 'w') as file:
        yaml.dump(pictrs, file)

# Done!
print('Done! You can now run the ansible playbook')
