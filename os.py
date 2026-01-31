
import subprocess
from getpass import getpass
from subprocess import call 
call("lsblk -f", shell=True)
disk = str(input("choose your disk: "))
disk_size = int(input("type in your disk size in gigabytes, e.g 128: "))
main_size = disk_size - 4
type = ""
while type not in ("mbr", "gpt"):
    type = str(input("partition type mbr or gpt?: "))

timezone = str(input("Type in your time zone city, e.g: Europe/Warsaw: "))
locale = (input("input your locale, e.g: pl_PL.UTF-8 UTF-8(leave empty for english): "))
if (len(locale) == 0):
    locale = "en_US.UTF-8 UTF-8"

keymap = str(input("Type in your keymap, e.g pl, de-latin1: "))
hostname = str(input("type in your machine hostname: "))

root_passwd = getpass("set your root password(hidden): ")
add_username = str(input("add another user? Leave empty if youre not adding a user: "))
if (len(add_username) > 0):
    user_passwd = getpass(f"set password for {add_username}: ")
    wheel_user = str(input("do your want to add the user to the wheel group? [y/n]: "))
    dm = str(input("do you want to install plasma? [y/n]: "))


    if dm == "y":
        dm_command = """
        pacman -S plasma sddm kde-applications --noconfirm
        systemctl enable sddm"""
else:
    user_passwd =""
    dm_command = ""
    dm = ""
    wheel_user = "n"
if wheel_user == "y":
    root_lock = input(f"you have created another user ({add_username}) and gave them sudo rights, do you want to lock the root account? [y/n]: ")
    if root_lock == "y":
        root_lock_command = """
        passwd -l root"""
    else:
        root_lock = ""
        root_lock_command = ""
else:
    root_lock = ""
if type == "gpt":
    sfdisk_input = f"""label: gpt
    size=1G type=U
    size={main_size}G, type=L
    type=S
    """
    subprocess.run(
        ["sfdisk", "--wipe", "always", "--wipe-partitions", "always", f"/dev/{disk}"],
        input=sfdisk_input,
        text=True)
    grub_gpt = """
    grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=arch
    grub-mkconfig -o /boot/grub/grub.cfg"""

elif type == "mbr":
    sfdisk_input = f"""label: mbr
    size={main_size}G, type=L
    type=S
    """
    subprocess.run(
        ["sfdisk", "--wipe", "always", "--wipe-partitions", "always", f"/dev/{disk}"],
        input=sfdisk_input,
        text=True)
    grub_mbr = f"""
    grub-install --target=i386-pc /dev/{disk} --bootloader-id=arch
    grub-mkconfig -o /boot/grub/grub.cfg"""
else:
    grub_gpt = ""
    grub_mbr = ""
if type == "gpt":
    if "nvme" in disk:
        call(f"mkfs.ext4 /dev/{disk}p2", shell=True)
        call(f"mkfs.fat -F32 /dev/{disk}p1", shell=True)
        call(f"mkswap /dev/{disk}p3", shell=True)
        call(f"mount /dev/{disk}p2 /mnt", shell=True)
        call(f"mount --mkdir /dev/{disk}p1 /mnt/boot", shell=True)
        call(f"swapon /dev/{disk}p3", shell=True)
    else:
        call(f"mkfs.ext4 /dev/{disk}2", shell=True)
        call(f"mkfs.fat -F32 /dev/{disk}1", shell=True)
        call(f"mkswap /dev/{disk}3", shell=True)
        call(f"mount /dev/{disk}2 /mnt", shell=True)
        call(f"mount --mkdir /dev/{disk}1 /mnt/boot", shell=True)
        call(f"swapon /dev/{disk}3", shell=True)
if type == "mbr":
    if "nvme" in disk:
        call(f"mkfs.ext4 /dev/{disk}p1", shell=True)
        call(f"mkswap /dev/{disk}p2", shell=True)
        call(f"mount /dev/{disk}p1 /mnt", shell=True)
        call(f"swapon /dev/{disk}p2", shell=True)
    else:
        call(f"mkfs.ext4 /dev/{disk}1", shell=True)
        call(f"mkswap /dev/{disk}2", shell=True)
        call(f"mount /dev/{disk}1 /mnt", shell=True)
        call(f"swapon /dev/{disk}2", shell=True)

subprocess.run(["pacman", "-Syu"], input="n\n", text=True)
call("pacman -S archlinux-keyring --noconfirm", shell=True)
call(f"pacstrap -K /mnt base linux linux-firmware", shell=True)
call("genfstab -U /mnt >> /mnt/etc/fstab", shell=True)
chroot_commands = f"""
echo 'KEYMAP={keymap}' >> /etc/vconsole.conf
echo 'LANG={locale.split()[0]}' >> /etc/locale.conf
echo '{locale}' >> /etc/locale.gen
locale-gen
ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime
hwclock --systohc
echo {hostname} >> /etc/hostname
mkinitcpio -P
pacman -S vim nano btop sudo grub efibootmgr networkmanager bash-completion htop --noconfirm
systemctl enable NetworkManager
"""

subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"{chroot_commands}"], check=True)
if type == "gpt":
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"{grub_gpt}" ], check=True)
elif type == "mbr":
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"{grub_mbr}" ], check=True)
if dm == "y":
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"{dm_command}" ], check=True)

subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"echo 'root:{root_passwd}' | chpasswd"], text=True)
if (len(add_username) > 0):
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"useradd -m {add_username}"], text=True)
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"echo '{add_username}:{user_passwd}' | chpasswd"], text=True)
if (wheel_user == "y"):
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"usermod -aG wheel {add_username}"],  text=True)
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", "echo '%wheel ALL=(ALL:ALL) ALL' >> /etc/sudoers"],  text=True)
if (root_lock == "y"):
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"{root_lock_command}"],  text=True)



call("umount -R /mnt", shell=True)
call("reboot", shell=True)














