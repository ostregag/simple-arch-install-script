
import subprocess
from getpass import getpass
from subprocess import call 
print("**********GPT AND UEFI ONLY FOR NOW**********")
call("lsblk -f", shell=True)
disk = str(input("choose your disk: "))
disk_size = int(input("type in your disk size in gigabytes, e.g 128: "))
main_size = disk_size - 4
#type = str(input("mbr or gpt?: "))
timezone = str(input("Type in your time zone city, e.g: Europe/Warsaw: "))
keymap = str(input("Type in your keymap, e.g pl, de-latin1: "))
root_passwd = getpass("set your root password(hidden): ")
add_username = str(input("add another user? Leave empty if youre not adding a user: "))
if (len(add_username) > 0):
    user_passwd = getpass(f"set password for {add_username}: ")
else:
    user_passwd =""
if (len(add_username) > 0):
    wheel_user = str(input("do your want to add the user to the wheel group? [y/n]: "))
else:
    wheel_user = "n"
hostname = str(input("type in your machine hostname: "))

#call(f"sfdisk /dev/{disk}", shell=True)
#if type == "gpt":
sfdisk_input = f"""label: gpt
size=1G type=U
size={main_size}G, type=L
type=S
"""
subprocess.run(
        ["sfdisk", "--wipe", "always", "--wipe-partitions", "always", f"/dev/{disk}"],
        input=sfdisk_input,
        text=True,)
#else: 
#    print ("wrong")
#    exit()
if "nvme" in disk:
    call(f"mkfs.ext4 /dev/{disk}p2", shell=True)
    call(f"mkfs.fat -F32 /dev/{disk}p1", shell=True)
    call(f"mkswap /dev/{disk}p3", shell=True)
else:
    call(f"mkfs.ext4 /dev/{disk}2", shell=True)
    call(f"mkfs.fat -F32 /dev/{disk}1", shell=True)
    call(f"mkswap /dev/{disk}3", shell=True)

call(f"mount /dev/{disk}2 /mnt", shell=True)
call(f"mount --mkdir /dev/{disk}1 /mnt/boot", shell=True)
call(f"swapon /dev/{disk}3", shell=True)
subprocess.run(["pacman", "-Syu"], input="n\n", text=True)
call("pacman -S archlinux-keyring --noconfirm", shell=True)
call(f"pacstrap -K /mnt base linux linux-firmware", shell=True)
call("genfstab -U /mnt >> /mnt/etc/fstab", shell=True)
chroot_commands = f"""
echo 'KEYMAP={keymap}' >> /etc/vconsole.conf
ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime
hwclock --systohc
echo {hostname} >> /etc/hostname
mkinitcpio -P
pacman -S vim nano btop sudo grub efibootmgr networkmanager bash-completion htop btop --noconfirm
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=arch
grub-mkconfig -o /boot/grub/grub.cfg
systemctl enable NetworkManager
"""
subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", chroot_commands], check=True)
subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"echo 'root:{root_passwd}' | chpasswd"], text=True)
if (len(add_username) > 0):
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"useradd -m {add_username}"], text=True)
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"echo '{add_username}:{user_passwd}' | chpasswd"], text=True)
if (wheel_user == "y"):
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", f"usermod -aG wheel {add_username}"],  text=True)
    subprocess.run(["arch-chroot", "/mnt", "/bin/bash", "-c", "echo '%wheel ALL=(ALL:ALL) ALL' >> /etc/sudoers"],  text=True)
call("exit", shell=True)
call("umount -R /mnt", shell=True)
call("reboot")














