# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np


class UnitConversion:
    # target_to_camera_dist = 56 m taken from https://scripts.iucr.org/cgi-bin/paper?S1600576719001730
    neutron_mass: float = 1.674927211e-27  # [kg]
    planck_h: float = 6.62606896e-34  # [JHz-1]
    angstrom: float = 1e-10  # [m]
    mega_electro_volt: float = 1.60217662e-19 / 1e6
    target_to_camera_dist: float = 56  # [m]
    data_offset: float = 0  # [s]
    tof_data_to_convert: np.ndarray
    velocity: np.ndarray

    def __init__(self, data_to_convert: np.ndarray | None = None) -> None:
        if data_to_convert is not None:
            self.set_data_to_convert(data_to_convert)
            self.check_data()

    def tof_seconds_to_wavelength_in_angstroms(self) -> np.ndarray:
        self.check_data()
        wavelength = self.planck_h / (self.neutron_mass * self.velocity)
        wavelength_angstroms = wavelength / self.angstrom
        return wavelength_angstroms

    def tof_seconds_to_energy(self) -> np.ndarray:
        self.check_data()
        energy = self.neutron_mass * self.velocity / 2
        energy_evs = energy / self.mega_electro_volt
        return energy_evs

    def tof_seconds_to_us(self) -> np.ndarray:
        self.check_data()
        return (self.tof_data_to_convert + self.data_offset) * 1e6

    def set_data_to_convert(self, data_to_convert: np.ndarray) -> None:
        self.tof_data_to_convert = data_to_convert

    def check_data(self) -> None:
        try:
            self.velocity = self.target_to_camera_dist / (self.tof_data_to_convert + self.data_offset)
        except AttributeError as exc:
            raise TypeError("No data to convert") from exc

    def set_data_offset(self, data_offset: float) -> None:
        self.data_offset = data_offset * 1e-6
