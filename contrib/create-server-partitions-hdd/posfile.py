"""

Create partitions on bare metal server for zfs storage.

Expected bare metal server with at least two *empty* HDD/SSD/NVMe in LiveCD mode.

Required inventory:

hosts.yaml:

    - new:                              # host alias
        host: "livecdip.example.com"    # ip or fqdn
        password: "example-password"    # password

vars.yaml:

    - new:                              # host alias
        boot: 1G                        # optional
        root: 8G                        # optional
        opt:  8G                        # optional
        tmp:  8G                        # optional
        var:  8G                        # optional
        devices:                        # devices to use
          - sda                         # required
          - sdb                         # required


# pos mkpart new

Example of created partitions:

sda                 8:0    0     4T  0 disk
├─sda1              8:1    0  1007K  0 part
├─sda2              8:2    0     1G  0 part
│ └─md0             9:0    0     1G  0 raid1
├─sda3              8:3    0    32G  0 part
│ └─md1             9:1    0    32G  0 raid1
│   ├─centos-root 252:0    0     8G  0 lvm
│   ├─centos-opt  252:1    0     8G  0 lvm
│   ├─centos-tmp  252:2    0     8G  0 lvm
│   └─centos-var  252:3    0     8G  0 lvm
└─sda4              8:4    0     4T  0 part
sdb                 8:16   0     4T  0 disk
├─sdb1              8:17   0  1007K  0 part
├─sdb2              8:18   0     1G  0 part
│ └─md0             9:0    0     1G  0 raid1
├─sdb3              8:19   0    32G  0 part
│ └─md1             9:1    0    32G  0 raid1
│   ├─centos-root 252:0    0     8G  0 lvm
│   ├─centos-opt  252:1    0     8G  0 lvm
│   ├─centos-tmp  252:2    0     8G  0 lvm
│   └─centos-var  252:3    0     8G  0 lvm
└─sdb4              8:20   0     4T  0 part

"""

__author__ = "Gena Makhomed"
__contact__ = "https://github.com/makhomed/possible"
__license__ = "GPLv3"
__version__ = "1.0.0"
__date__ = "2020-05-09"


import sys
import time

from possible import task, allow, Context


SECTOR_SIZE_IN_BYTES = 512

SECTORS_IN_ONE_GIB = 1024 * 1024 * 1024 // SECTOR_SIZE_IN_BYTES

SECTORS_IN_ONE_MIB = 1024 * 1024 // SECTOR_SIZE_IN_BYTES

GPT_SIZE_IN_SECTORS = 34

BIOS_GRUB_SIZE_IN_SECTORS = 2014


def round_up(val, base):
    return (val + base - 1) & ~(base - 1)


def gib_to_sectors(size_in_gib):
    return size_in_gib * SECTORS_IN_ONE_GIB


def partition(device, number):
    if device.startswith('sd'):
        return device + str(number)
    elif device.startswith('nvme'):
        return device + "p" + str(number)
    else:
        raise TypeError(f"Unknown device '{device}' type.")


class Parted:
    def __init__(self, c, devices):
        self.c = c
        self.devices = devices
        self.offset = GPT_SIZE_IN_SECTORS
        self.part_index = 1
        self.partitions = list()

    def _choose_bitmap_space(self, devsize):
        """
         * if the device is bigger than 8Gig, save 64k for bitmap usage,
         * if bigger than 200Gig, save 128k
         * NOTE: result must be multiple of 4K else bad things happen
         * on 4K-sector devices.
        """
        if devsize < 64*2:
            return 0
        if devsize - 64*2 >= 200*1024*1024*2:
            return 128*2
        if devsize - 4*2 > 8*1024*1024*2:
            return 64*2
        return 4*2

    def _mdraid_metadata_size_in_sectors(self, data_size_in_sectors):  # pylint: disable=no-self-use
        """Return mdraid metadata size in sectors for data_size_in_sectors
           metadata size is at least 1Mib for alignment
           metadata size is 0.1% of data size, but no more than 128MiB.
        """
        assert data_size_in_sectors > 0
        headroom = 128 * SECTORS_IN_ONE_MIB
        while (headroom << 10) > data_size_in_sectors:
            headroom >>= 1
        bmspace = self._choose_bitmap_space(data_size_in_sectors)
        data_offset = 12 * 2 + bmspace + headroom
        data_offset = round_up(data_offset, SECTORS_IN_ONE_MIB)
        return data_offset

    def _lvm_metadata_size_in_sectors(self, data_size_in_sectors):  # pylint: disable=no-self-use
        assert data_size_in_sectors > 0
        return 2048

    def mkpart(self, description, data_size_in_sectors, mdraid, lvm):
        if data_size_in_sectors == -1:
            start = self.offset
            end = -34
            self.offset = 2**128 - 1
        else:
            if mdraid:
                data_size_in_sectors += self._mdraid_metadata_size_in_sectors(data_size_in_sectors)
            if lvm:
                data_size_in_sectors += self._lvm_metadata_size_in_sectors(data_size_in_sectors)
            start = self.offset
            end = self.offset + data_size_in_sectors - 1
            self.offset = self.offset + data_size_in_sectors
        part = (self.part_index, start, end, description)
        self.partitions.append(part)
        self.part_index = self.part_index + 1

    def check_alignment(self, align_in_sectors=2048):
        print()
        print('check partition align at %dKiB:' % (align_in_sectors / 2))
        print('----------------------------')
        for device in self.devices:
            for part_index, start, dummy_end, dummy_description in self.partitions:
                if start % align_in_sectors == 0:
                    print("    partition %s%d aligned" % (device, part_index))
                else:
                    print("    partition %s%d NOT aligned" % (device, part_index))

    def _commit(self, print_only):
        print
        for device in self.devices:
            if print_only:
                print("parted -s /dev/%s mklabel gpt" % device)
            else:
                self.c.run("parted -s /dev/%s mklabel gpt" % device)
        print
        for device in self.devices:
            for dummy_part_index, start, end, dummy_description in self.partitions:
                if print_only:
                    print("parted -s /dev/%s -a min -- mkpart primary %ds %ds" % (device, start, end))
                else:
                    self.c.run("parted -s /dev/%s -a min -- mkpart primary %ds %ds" % (device, start, end))
            print

    def out(self):
        self._commit(print_only=True)

    def run(self):
        self._commit(print_only=False)


class PartMan:
    def __init__(self, hosts):
        assert len(hosts) == 1
        host = hosts[0]
        self.c = Context(host)
        self.boot_size_in_gib = int(self.c.var('boot', '1G').rstrip('G'))
        self.root_size_in_gib = int(self.c.var('root', '8G').rstrip('G'))
        self.opt_size_in_gib = int(self.c.var('opt', '8G').rstrip('G'))
        self.tmp_size_in_gib = int(self.c.var('tmp', '8G').rstrip('G'))
        self.var_size_in_gib = int(self.c.var('var', '8G').rstrip('G'))
        self.lvm_size_in_gib = self.root_size_in_gib + self.opt_size_in_gib + self.tmp_size_in_gib + self.var_size_in_gib
        self.devices = set(self.c.var('devices'))
        assert len(self.devices) >= 2

    def parts(self, number):
        out = list()
        for device in sorted(self.devices):
            out.append(f"/dev/{partition(device, number)}")
        return " ".join(out)

    def is_live_cd(self):
        out = self.c.run("mount").stdout
        lines = out.split("\n")
        for line in lines:
            if line.startswith("overlay on / type overlay"):
                return True
            if line.startswith("airootfs on / type overlay"):
                return True
            if line.startswith("aufs on / type aufs"):
                return True
        return False

    def is_devices_has_no_partitions(self):
        stdout = self.c.run("lsblk --noheadings --output NAME,TYPE --raw").stdout
        devices = set()
        for line in stdout.split('\n'):
            line = line.strip()
            if line == '':
                continue
            device_name, device_type = line.split()
            if device_type == 'loop' or device_type == 'rom':
                continue
            if device_type == 'disk':
                devices.add(device_name)
            if device_type == 'part':
                return False
        assert self.devices <= devices
        return True

    def lspart(self):
        if not self.is_live_cd():
            raise RuntimeError("Not in LiveCD mode")
        print()
        print(self.c.run('lsblk').stdout)
        print()
        if self.is_devices_has_no_partitions():
            print(f"Devices {self.devices} has no partitions.")

    def mkpart(self):
        if not self.is_live_cd():
            raise RuntimeError("Not in LiveCD mode")
        if not self.is_devices_has_no_partitions():
            print(f"Devices {self.devices} already has partitions:")
            print()
            print(self.c.run('lsblk').stdout)
            print()
            print("Nothing to do.")
            sys.exit(1)

        parted = Parted(self.c, self.devices)
        parted.mkpart('for bios_grub', BIOS_GRUB_SIZE_IN_SECTORS, mdraid=False, lvm=False)
        parted.mkpart('for  /dev/md0', gib_to_sectors(self.boot_size_in_gib), mdraid=True, lvm=False)
        parted.mkpart('for  /dev/md1', gib_to_sectors(self.lvm_size_in_gib), mdraid=True, lvm=True)
        parted.mkpart('for zfs zpool', -1, mdraid=False, lvm=False)
        parted.run()

        for device in self.devices:
            self.c.run(f"parted -s /dev/{device} -- set 1 bios_grub on")
            self.c.run(f"parted -s /dev/{device} -- set 2 raid on")
            self.c.run(f"parted -s /dev/{device} -- set 3 raid on")

        time.sleep(1)

        self.c.run(f"mdadm --create /dev/md0 --level=mirror --raid-devices={len(self.devices)} {self.parts(2)} --metadata=1.2")
        self.c.run(f"mdadm --create /dev/md1 --level=mirror --raid-devices={len(self.devices)} {self.parts(3)} --metadata=1.2")

        self.c.run("pvcreate /dev/md1")

        self.c.run("vgcreate centos /dev/md1")

        self.c.run(f"lvcreate -n root -L {self.root_size_in_gib}G centos")
        self.c.run(f"lvcreate -n  opt -L {self.opt_size_in_gib}G centos")
        self.c.run(f"lvcreate -n  tmp -L {self.tmp_size_in_gib}G centos")
        self.c.run(f"lvcreate -n  var -L {self.var_size_in_gib}G centos")
        print()
        print(self.c.run('lsblk').stdout)
        print()
        print("Done.")

    def rmpart(self):
        if not self.is_live_cd():
            raise RuntimeError("Not in LiveCD mode")
        print()
        print(self.c.run('lsblk').stdout)
        print()
        if self.is_devices_has_no_partitions():
            print(f"Devices {self.devices} has no partitions.")
            sys.exit(0)
        else:
            s = input("Delete ALL partitions? [YES/NO]: ")
            if s != 'YES':
                sys.exit(1)

        self.c.run("lvremove -f centos", can_fail=True)
        self.c.run("vgremove -f centos", can_fail=True)
        self.c.run("pvremove -f /dev/md1", can_fail=True)

        self.c.run("mdadm --stop /dev/md0", can_fail=True)
        self.c.run(f"mdadm --zero-superblock {self.parts(2)}", can_fail=True)
        self.c.run("mdadm --stop /dev/md1", can_fail=True)
        self.c.run(f"mdadm --zero-superblock {self.parts(3)}", can_fail=True)

        for device in self.devices:
            self.c.run(f"parted -s /dev/{device} -- rm 1", can_fail=True)
            self.c.run(f"parted -s /dev/{device} -- rm 2", can_fail=True)
            self.c.run(f"parted -s /dev/{device} -- rm 3", can_fail=True)
            self.c.run(f"parted -s /dev/{device} -- rm 4", can_fail=True)

        print()
        print(self.c.run('lsblk').stdout)
        print()
        print("Done.")


@task
@allow('new')
def lspart(hosts):
    """show   partitions"""
    PartMan(hosts).lspart()


@task
@allow('new')
def mkpart(hosts):
    """create partitions"""
    PartMan(hosts).mkpart()


@task
@allow('new')
def rmpart(hosts):
    """remove partitions"""
    PartMan(hosts).rmpart()
