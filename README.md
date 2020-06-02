# KVMD-Auth-Server
[![CI](https://github.com/pikvm/kvmd-auth-server/workflows/CI/badge.svg)](https://github.com/pikvm/kvmd-auth-server/actions?query=workflow%3ACI)
[![Discord](https://img.shields.io/discord/580094191938437144?logo=discord)](https://discord.gg/bpmXfz5)

This repository demonstrates the ability to organize a centralized HTTP authorization server for Pi-KVM with a single user database.
It's assumed that you already have a MySQL server that used to store user's credentials.
Please note that passwords are stored in plain text. In addition, passwords are transmitted over the network over HTTP, not HTTPS.
This server only demonstrates how authorization works.
In a real secure infrastructure we recommend that you salt passwords and hash them and configure HTTPS.

-----
# The process

When using HTTP authorization, [KVMD](https://github.com/pikvm/kvmd) sends the following
[JSON POST request](https://github.com/pikvm/kvmd/blob/master/kvmd/plugins/auth/http.py) to the server specified
in the settings (for example `http://kvmauth/auth`):
```json
    {
        "user": "<username>",
        "passwd": "<qwerty>",
        "secret": "<12345>"
    }
```

This request contains the name of the user who wants to log in to Pi-KVM, his password, and a "secret" that appears in KVMD config.
In our case, it's used as a KVM ID in the network. Based on this secret, the server will decide whether the user is allowed access to a specific KVM.

If the auth server responds with `200 OK`, KVMD will allow the user to log in.
For other response codes, the login will be denied.

----
# HOWTO
1. Create MySQL database `kvm_users` and allow the `kvmauth` user access to this database.

2. Create table:
```sql
CREATE TABLE kvm_users (
    id INT(32) NOT NULL AUTO_INCREMENT,
    kvm_id VARCHAR(50) NOT NULL,
    user VARCHAR(50) NOT NULL,
    passwd VARCHAR(60) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY user (user)
);
```

3. Add an `example` user:
    ```sql
    INSERT INTO kvm_users (kvm_id, user, passwd) VALUES ("12345", "example", "pa$$word");
    ```

4. Clone this repo to your server:
    ```bash
    $ git clone https://github.com/pikvm/kvmd-auth-server
    ```

5. Edit `config.yaml`. Set DB and auth server params. It will listen `server.host` and `server.port` for upcoming requests from Pi-KVM devices.

6. Run and run server:
    ```bash
    $ make build
    $ make run
    ```

6. Edit `/etc/kvmd/auth.yaml` on your Pi-KVM and reboot it:
    ```yaml
    internal:
        force_users: admin
    external:
        type: http
        url: http://your_auth_server:port/auth
        secret: 12345  # KVM ID
    ````

    The `admin` user will be checked through local KVM auth. Any other users will only be logged in through the auth server.
    
-----
# License
Copyright (C) 2018 by Maxim Devaev mdevaev@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see https://www.gnu.org/licenses/.
