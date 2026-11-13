---
name: system
description: Working with PCP OS itself - building, starting and inspecting its kernel in a virtual machine, reading its self-test log, looking up a state machine's table, or explaining what PCP OS can and cannot do today. Use for questions about the operating system, not for running a review.
---

# PCP OS

PCP OS is in early development. Say what exists, and no more. Describing the system does not put ACR in use.

**Exists, and was started in QEMU:** a new kernel for x86_64 written in Rust. It protects its own memory and shows the protection by attempting the forbidden accesses, handles exceptions and a timer, runs the native ACR guards, and keeps a register of its own start, verification, processes and stop. It runs thirteen small programs built into its image as processes in user mode, and it loads ordinary programs from files handed to it beside the kernel: statically linked, position-independent programs for x86_64 that speak the system-call conventions of Linux. It checks each before running it, gives each its own address space and only the devices the session granted, and drives an emulated display, keyboard and two sound devices. It shows a launcher of its own and keeps one key, Ctrl+Alt+Del, that ends the running program. The program used to test all of this is Doom, which is a separate program under its own licence and is not part of PCP OS. Named an expected measurement of its image when it is started, the kernel compares its own with it; a kernel that fails its verification starts no program.

**Does not exist:** storage that survives a stop, a network, a mouse, a shell, users, more than one program on the screen at a time, a second processor. Every device it drives is an emulated one, and it has not been started on a real computer. The system calls it answers are the ones two programs needed. Nothing in it is certified for any use, and it is not fit for use where a failure can harm people.

**On another operating system**, which is where you are now, the same core runs as an ordinary program: the tool server behind the `acr_` tools, and the hooks that record what the host observes. That program is as trustworthy as the system it runs on. It binds your tool calls; it cannot bind anything that writes the register file directly. Closing that gap is what the kernel is for. The kernel can run a program now; it cannot yet run this one, or an assistant.

## State machines

`acr_machine` prints the whole table of one machine: SYSTEM, USE, REVIEW, OBJECTION, OBLIGATION, TASK, DELIVERY, LINK. For each state and event it gives the next state, or `-` for not accepted. A table entry says what would follow. It does not show that a transition happened: that is in the register.

## Starting the kernel

From the PCP OS Rust workspace, with a Rust toolchain that has its sources, `ld.lld`, `objcopy` and `qemu-system-x86_64`:

```
crates/pcpos-kernel/run.sh
```

QEMU's exit status 33 means every self-test passed. Read the log; do not report a pass you did not read. The serial port is the only channel: there is no guest agent, and nothing can be sent to the kernel.
