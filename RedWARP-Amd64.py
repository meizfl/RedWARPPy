import os
import platform
import subprocess

def manual_mode():
    """Function for manual input of parameters"""
    custom_endpoint = input("Enter Endpoint (for example, 162.159.193.5:4500): ")
    if not custom_endpoint:
        custom_endpoint = "162.159.193.5:4500"

    custom_mtu = input("Enter value MTU (by default - 1420): ")
    if not custom_mtu:
        custom_mtu = "1420"

    ipv6_enabled = input("Will the config support IPv6? (y/n, by default y): ")
    if ipv6_enabled != "n":
        ipv6_enabled = "y"
    return custom_endpoint, custom_mtu, ipv6_enabled

# Determining the processor architecture
arch = platform.machine()

# Set the path to the wgcf binary depending on the architecture

wgcf_path = "./bin/wgcf_amd64"

if not wgcf_path:
    print(
        f"Unknown or unsupported architecture: {arch}. Supported x86_64, i386, arm64, armv7, armv6, armv5, mips, mips64, mipsle, mips64le, s390x."
    )
    exit(1)

# Check that the selected wgcf binary exists
if not os.path.isfile(wgcf_path):
    print(
        f"Binary file {wgcf_path} not found. Make sure it exists and is accessible."
    )
    exit(1)

# Let's make sure wgcf can be run
os.chmod(wgcf_path, 0o755)

# Operating mode: automatic or manual
mode = input(
    "Select mode: 'a'(auto) for automatic setup or 'm'(manual) for manual input (default 'a'): "
)
if mode == "m":
    custom_endpoint, custom_mtu, ipv6_enabled = manual_mode()
else:
    custom_endpoint = "162.159.193.5:4500"
    custom_mtu = "1420"
    ipv6_enabled = "y"

# Generating a configuration file using wgcf
subprocess.run([wgcf_path, "register", "--accept-tos"], check=True)
subprocess.run([wgcf_path, "generate"], check=True)

# Check if the generated wgcf-profile.conf file exists
if not os.path.isfile("wgcf-profile.conf"):
    print("Could not find generated configuration file wgcf-profile.conf")
    exit(1)

# Изменение конфигурационного файла:
with open("wgcf-profile.conf", "r") as f:
    lines = f.readlines()

with open("wgcf-profile.conf", "w") as f:
    interface_section = False
    for line in lines:
        if line.startswith("[Interface]"):
            interface_section = True
        elif line.startswith("["):  # Начало другой секции
            interface_section = False

        if interface_section and line.startswith("PrivateKey ="):
            f.write(line)
            f.write(
                "S1 = 0\nS2 = 0\nJc = 120\nJmin = 23\nJmax = 911\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\n"
            )
        elif line.startswith("MTU = "):
            f.write(f"MTU = {custom_mtu}\n")
        elif line.startswith("Endpoint = "):
            f.write(f"Endpoint = {custom_endpoint}\n")
        elif ipv6_enabled == "n" and (line.startswith("Address = 2606:4700") or line.startswith("AllowedIPs = ::/0")):
            continue  # Пропускаем только строки с IPv6 адресами
        elif line.startswith("DNS = ") and ipv6_enabled == "n":
            f.write("DNS = 208.67.222.222, 208.67.220.220\n")
        elif line.startswith("DNS = ") and ipv6_enabled == "y":
            f.write(
                "DNS = 208.67.222.222, 208.67.220.220, 2620:119:35::35, 2620:119:53::53\n"
            )
        else:
            f.write(line)

# Renaming to RedWARP.conf
os.rename("wgcf-profile.conf", "RedWARP.conf")

# Checking for successful modification
with open("RedWARP.conf", "r") as f:
    content = f.read()

if (
    "S1 = 0" in content
    and f"MTU = {custom_mtu}" in content
    and f"Endpoint = {custom_endpoint}" in content
    and (
        ("DNS = 208.67.222.222, 208.67.220.220" in content)
        or (
            "DNS = 208.67.222.222, 208.67.220.220, 2620:119:35::35, 2620:119:53::53"
            in content
        )
    )
):
    print("Configuration successfully updated and saved to RedWARP.conf!")
else:
    print("An error occurred while updating the configuration.")
