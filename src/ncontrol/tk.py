"""Compact stopped rotary controls for large integer parameter traversals."""
from __future__ import annotations

import math


class NDimensionalKnob:
    """Tk Canvas knob with coarse/fine/ultrafine integer stepping.

    The primary dial maps its 270 degree sweep to the complete traversal. Small
    step buttons provide precise movement without requiring a physically long
    slider. The model remains framework-independent in nd_control.py.
    """
    def __init__(self, parent, *, maximum, value, command, tk, ttk, diameter=92,
                 minimum_interval_ms=80, auto_scan_controller=None,
                 interval_label_prefix='Interval (ms)', auto_scan_enabled=True):
        self.maximum = max(0, int(maximum))
        self.value = max(0, min(self.maximum, int(value)))
        self.command = command
        self.tk, self.ttk = tk, ttk
        self.frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.frame, width=diameter, height=diameter,
                                highlightthickness=0)
        self.canvas.pack(side='left', padx=(0, 8))
        self.diameter = diameter
        self.canvas.bind('<Button-1>', self._pointer)
        self.canvas.bind('<B1-Motion>', self._pointer)
        self.canvas.bind('<MouseWheel>', self._wheel)
        controls = ttk.Frame(self.frame)
        controls.pack(side='left', fill='x', expand=True)
        self.readout = tk.StringVar()
        self.auto_scan = tk.BooleanVar(value=False)
        self.scan_delay_ms = tk.IntVar(value=700)
        self.scan_step = tk.IntVar(value=max(1, self.maximum // 1000))
        self._auto_after_id = None
        self.minimum_interval_ms = max(1, int(minimum_interval_ms))
        self.auto_scan_controller = auto_scan_controller
        self.interval_label_prefix = interval_label_prefix
        self.auto_scan_enabled = bool(auto_scan_enabled)
        ttk.Label(controls, textvariable=self.readout).pack(anchor='w')
        # Roughly 1/1000 and 1/1,000,000 of the complete path, plus exact states.
        self.steps = tuple(max(1, self.maximum // divisor)
                           for divisor in (1000, 1_000_000)) + (1,)
        for label, step in zip(('Fine', 'Ultrafine', 'State'), self.steps):
            row = ttk.Frame(controls)
            row.pack(fill='x', pady=1)
            ttk.Label(row, text=label, width=10).pack(side='left')
            ttk.Button(row, text='−', width=3,
                       command=lambda s=step: self.nudge(-s)).pack(side='left')
            ttk.Button(row, text='+', width=3,
                       command=lambda s=step: self.nudge(s)).pack(side='left')
            ttk.Label(row, text=f'±{step:,}').pack(side='left', padx=4)

        auto = ttk.Frame(controls)
        auto.pack(fill='x', pady=(5, 0))
        self.auto_scan_check = ttk.Checkbutton(
            auto,
            text='Auto scan',
            variable=self.auto_scan,
            command=self._toggle_auto_scan,
        )
        self.auto_scan_check.pack(side='left')
        if not self.auto_scan_enabled:
            self.auto_scan.set(False)
            self.auto_scan_check.state(['disabled'])

        step_row = ttk.Frame(controls)
        step_row.pack(fill='x', pady=(2, 0))
        ttk.Label(step_row, text='Step size', width=11).pack(side='left')
        self.scan_step_entry = ttk.Entry(step_row, textvariable=self.scan_step, width=10)
        self.scan_step_entry.pack(side='left', padx=(0, 4))
        self.scan_step_scale = ttk.Scale(
            step_row, from_=1, to=max(1, self.maximum), variable=self.scan_step
        )
        self.scan_step_scale.pack(side='left', fill='x', expand=True)
        if not self.auto_scan_enabled:
            self.scan_step_entry.state(['disabled'])
            self.scan_step_scale.state(['disabled'])

        interval = ttk.Frame(controls)
        interval.pack(fill='x', pady=(2, 0))
        self.interval_label = tk.StringVar()
        ttk.Label(interval, textvariable=self.interval_label, width=22).pack(side='left')
        self.interval_entry = ttk.Entry(interval, textvariable=self.scan_delay_ms, width=10)
        self.interval_entry.pack(side='left', padx=(0, 4))
        self.interval_scale = ttk.Scale(
            interval,
            from_=self.minimum_interval_ms,
            to=max(2000, self.minimum_interval_ms * 4),
            variable=self.scan_delay_ms,
        )
        self.interval_scale.pack(side='left', fill='x', expand=True)
        if not self.auto_scan_enabled:
            self.interval_entry.state(['disabled'])
            self.interval_scale.state(['disabled'])

        self.set_minimum_interval(self.minimum_interval_ms)
        self.draw()

    def set_minimum_interval(self, milliseconds):
        minimum = max(1, int(math.ceil(milliseconds)))
        self.minimum_interval_ms = minimum
        self.interval_label.set(f'{self.interval_label_prefix} · min {minimum}')
        self.interval_scale.configure(
            from_=minimum,
            to=max(2000, minimum * 4),
        )
        try:
            if int(self.scan_delay_ms.get()) < minimum:
                self.scan_delay_ms.set(minimum)
        except (ValueError, self.tk.TclError):
            self.scan_delay_ms.set(minimum)
        if self.auto_scan.get():
            self._start_auto_scan()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def set(self, value, *, notify=False):
        new = max(0, min(self.maximum, int(round(value))))
        changed = new != self.value
        self.value = new
        self.draw()
        if notify and changed:
            self.command(new)

    def nudge(self, amount):
        self.set(self.value + amount, notify=True)

    def _toggle_auto_scan(self):
        if not self.auto_scan_enabled:
            self.auto_scan.set(False)
            self._stop_auto_scan()
            return
        if self.auto_scan_controller is not None:
            self._stop_auto_scan()
            self.auto_scan_controller(self, bool(self.auto_scan.get()))
            return
        if self.auto_scan.get():
            self._start_auto_scan()
        else:
            self._stop_auto_scan()

    def _start_auto_scan(self):
        self._stop_auto_scan()
        if not self.auto_scan.get():
            return
        try:
            delay = max(self.minimum_interval_ms, int(self.scan_delay_ms.get()))
            if int(self.scan_delay_ms.get()) != delay:
                self.scan_delay_ms.set(delay)
        except (ValueError, self.tk.TclError):
            delay = 700
            self.scan_delay_ms.set(delay)
        self._auto_after_id = self.frame.after(delay, self._auto_tick)

    def _stop_auto_scan(self):
        if self._auto_after_id is None:
            return
        try:
            self.frame.after_cancel(self._auto_after_id)
        except self.tk.TclError:
            pass
        self._auto_after_id = None

    def _auto_tick(self):
        self._auto_after_id = None
        try:
            if not self.frame.winfo_exists() or not self.auto_scan.get():
                return
            if self.maximum > 0:
                try:
                    step = int(self.scan_step.get())
                except (ValueError, self.tk.TclError):
                    step = 1
                    self.scan_step.set(step)
                step = max(1, min(self.maximum, step))
                target = self.value + step
                if target > self.maximum:
                    target = 0
                self.set(target, notify=True)
            self._start_auto_scan()
        except self.tk.TclError:
            self._auto_after_id = None

    def _wheel(self, event):
        self.nudge(self.steps[0] if event.delta > 0 else -self.steps[0])

    def _pointer(self, event):
        c = self.diameter / 2
        angle = math.degrees(math.atan2(event.y-c, event.x-c))
        # Dial runs clockwise from 225 degrees to -45 degrees, leaving a bottom gap.
        clockwise = (angle - 135.0) % 360.0
        clockwise = min(270.0, clockwise)
        position = clockwise / 270.0
        self.set(round(position*self.maximum), notify=True)

    def draw(self):
        canvas = self.canvas
        canvas.delete('all')
        d, pad = self.diameter, 8
        canvas.create_arc(pad, pad, d-pad, d-pad, start=-45, extent=270,
                          style='arc', width=4)
        position = 0 if not self.maximum else self.value/self.maximum
        angle = math.radians(225 - 270*position)
        c, radius = d/2, d*.31
        canvas.create_oval(c-d*.27, c-d*.27, c+d*.27, c+d*.27, width=2)
        canvas.create_line(c, c, c+radius*math.cos(angle), c-radius*math.sin(angle),
                           width=3)
        self.readout.set(f'{self.value:,} / {self.maximum:,}')
