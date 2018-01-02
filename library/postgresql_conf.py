#!/usr/bin/python

DOCUMENTATION = '''
module: postgresql_conf
short_description: modify the postgresql configuration
requirements: [ pg_conftool ]
options:
    key:
        description:
            - The parameter name to modify
        required: true
        default: none
    value:
        description:
            - The parameter value, for present and append state
        required: false
        default: none
    state:
        description:
            - Whether the parameter should be there or not. The append state
            allow multiple values, separated by a comma.
        choices: [ present, absent, append ]
        required: false
        default: present
'''

EXAMPLES = '''
- postgresql_conf:
    key: bonjour
    state: absent

- postgresql_conf:
    key: max_connections
    value: 100
    state: present

- postgresql_conf:
    key: shared_preload_libraries
    value: powa
    state: append
'''

from ansible.module_utils.basic import *
import subprocess
import re

def pg_conftool(action, parameter, value=None):
    if value == None:
        current = subprocess.check_output(['pg_conftool', '--short', action, parameter])
    else:
        current =  subprocess.check_output(['pg_conftool', '--short', action, parameter, value])

    return current.strip('\n')

def is_absent(parameter):
    try:
        pg_conftool('show', parameter)
        return False
    except subprocess.CalledProcessError:
        return True

def is_append(parameter, value):
    try:
        current = pg_conftool('show', parameter)
        return re.search('[^|,]' + value + '[,$]', current) != None
    except subprocess.CalledProcessError:
        return False

def is_present(parameter, value):
    try:
        return pg_conftool('show', parameter) == value
    except subprocess.CalledProcessError:
        return False

def absent(parameter):
    if not is_absent(parameter):
        pg_conftool('remove', parameter)
        return True
    return False

def append(parameter, value):
    if not is_append(parameter, value):
        try:
            current = pg_conftool('show', parameter)
            pg_conftool('set', parameter, current + ',' + value)
        except subprocess.CalledProcessError:
            pg_conftool('set', parameter, value)

        return True
    return False

def present(parameter, value):
    if not is_present(parameter, value):
        pg_conftool('set', parameter, value)
        return True
    return False

def main():
    module = AnsibleModule(
        argument_spec = {
            'key': { 'required': True },
            'value': {},
            'state': {
                'default': 'present',
                'choices': ['present', 'absent', 'append']
            },
        },
        supports_check_mode = True
    )

    key = module.params['key']
    value = module.params['value']
    state = module.params['state']

    module.get_bin_path('pg_conftool', True)

    if module.check_mode:
        if state == 'absent':
            changed = not is_absent(key)
        elif state == 'append':
            changed = not is_append(key, value)
        elif state == 'present':
            changed = not is_present(key, value)
    else:
        if state == 'absent':
            changed = absent(key)
        elif state == 'append':
            changed = append(key, value)
        elif state == 'present':
            changed = present(key, value)

    module.exit_json(changed = changed)

if __name__ == '__main__':
    main()
