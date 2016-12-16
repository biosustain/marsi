# Copyright 2016 Chr. Hansen A/S and The Novo Nordisk Foundation Center for Biosustainability, DTU.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import time

from functools import lru_cache

import numpy as np

import pybel
from bitarray import bitarray

from marsi.processing.chemistry.common import convex_hull_volume, monte_carlo_volume as mc_vol

__all__ = ['has_radical', 'mol_to_inchi', 'mol_to_inchi_key', 'mol_to_svg', 'mol_chebi_id', 'mol_drugbank_id',
           'mol_pubchem_id', 'mol_str_to_inchi', 'align_molecules', 'inchi_to_molecule', 'smiles_to_molecule',
           'fingerprint', 'fingerprint_to_bits', 'get_spectrophore_data', 'inchi_to_inchi_key', 'solubility']


def has_radical(mol):
    """
    Finds if a pybel.Molecule has Radicals.
    Radicals have an atomic number of 0.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    bool
        True if there are any radicals.
    """
    return any(a.atomicnum == 0 for a in mol.atoms)


def mol_to_inchi(mol):
    """
    Makes an InChI from a pybel.Molecule.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    str
        A InChI string.
    """
    return mol.write(format="inchi", opt=dict(errorlevel=0)).strip()


def mol_to_svg(mol):
    """
    Makes an SVG from a pybel.Molecule.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    str
        A SVG string.
    """
    return mol.write(format="svg", opt=dict(errorlevel=0)).strip()


def mol_to_inchi_key(mol):
    """
    Makes an InChI Key from a pybel.Molecule.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    str
        A InChI key.
    """
    return mol.write(format="inchikey", opt=dict(errorlevel=0)).strip()


@lru_cache(maxsize=256)
def inchi_to_inchi_key(inchi):
    """
    Makes an InChI Key from a InChI string.

    Arguments
    ---------
    inchi: str
        A valid InChI string.

    Returns
    -------
    str
        A InChI key.
    """
    return mol_to_inchi_key(inchi_to_molecule(inchi))


def mol_drugbank_id(mol):
    """
    Returns the DrugBank ID from the molecule data.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    str
       DrugBank ID
    """
    return mol.data['DRUGBANK_ID'].strip()


def mol_pubchem_id(mol):
    """
    Returns the PubChem Compound ID from the molecule data.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    str
       PubChem Compound ID
    """
    return mol.data['PUBCHEM_COMPOUND_CID'].strip()


def mol_chebi_id(mol):
    """
    Returns the ChEBI ID from the molecule data.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.

    Returns
    -------
    str
       ChEBI ID
    """
    return mol.data['ChEBI ID'].strip()


def fingerprint(mol, fpformat='maccs'):
    """
    Returns the Fingerprint of the molecule.

    Arguments
    ---------
    mol: pybel.Molecule
        A molecule.
    fpformat: str
        A valid fingerprint format (see pybel.fps)

    Returns
    -------
    pybel.Fingerprint
        A fingerprint
    """
    if fpformat not in pybel.fps:
        raise AssertionError("'%s' is not a valid fingerprint format" % fpformat)
    return mol.calcfp(fptype=fpformat)


@lru_cache(maxsize=256)
def inchi_to_molecule(inchi):
    """
    Returns a molecule from a InChI string.

    Arguments
    ---------
    inchi: str
        A valid string.

    Returns
    -------
    mol: pybel.Molecule
        A molecule.
    """
    mol = pybel.readstring('inchi', inchi, opt=dict(errorlevel=0))
    mol.addh()
    return mol


def mol_str_to_inchi(mol_str):
    """
    Returns the InChI from the molecule data.

    Arguments
    ---------
    mol_str: str
        A valid MOL string.

    Returns
    -------
    str
        A InChI string.
    """
    mol_to_inchi(pybel.readstring('mol', mol_str))


def smiles_to_molecule(smiles):
    """
    Returns the pybel.Molecule from the molecule data.

    Arguments
    ---------
    simes: str
        A valid SMILES string.

    Returns
    -------
    pybel.Molecule
        A Molecule.
    """
    return pybel.readstring('smi', smiles)


def fingerprint_to_bits(fp, bits=1024):
    """
    Converts a pybel.Fingerprint into a binary array

    Arguments
    ---------
    fp: pybel.Fingerprint
        A fingerprint molecule.

    bits: int
        Number of bits (default is 1024)
    Returns
    -------
    list
    """
    bits_list = bitarray(bits)

    for i in fp.bits:
        if i <= bits:
            bits_list[i-1] = 1

    return bits_list


def align_molecules(reference, *molecules, include_h=True, symmetry=True):
    """
    Align molecules to a reference.

    Arguments
    ---------
    reference: pybel.Molecule
        A reference molecule.
    molecules: pybel.Molecule
        Molecules to align.
    include_h: bool
        Include implicit hydrogen atoms.
    symmetry: bool

    Returns
    -------
    list
    """

    align = pybel.ob.OBAlign
    return [align(reference, molecule, include_h, symmetry) for molecule in molecules]


def get_spectrophore_data(molecule):
    """
    A Spectrophore is calculated as a vector of 48 numbers (in the case of a non-stereospecific Spectrophore.
    The 48 doubles are organised into 4 sets of 12 doubles each:
    * numbers 01-11: Spectrophore values calculated from the atomic partial charges;
    * numbers 13-24: Spectrophore values calculated from the atomic lipophilicity properties;
    * numbers 25-36: Spectrophore values calculated from the atomic shape deviations;
    * numbers 37-48: Spectrophore values calculated from the atomic electrophilicity properties;

    Arguments
    ---------
    molecule: pybel.Molecule

    Returns
    -------
    ndarray:
        Float 1D-Array with the 48 features generated by OBSpectrophore.
    """
    spectrophore = pybel.ob.OBSpectrophore()

    return np.array(spectrophore.GetSpectrophore(molecule.OBMol), dtype=np.float32)


def solubility(molecule, log_value=True):
    """
    ESOL:  Estimating Aqueous Solubility Directly from Molecular Structure [1]

        $Log(S_w) = 0.16 - 0.63 logP - 0.0062 MWT + 0.066 RB - 0.74 AP$
        MWT = Molecular Weight
        RB = Rotatable Bounds
        AP = Aromatic Proportion
        ogP

    Arguments
    ---------
    molecule: pybel.Molecule

    Returns
    -------
    float
        log(S_w): log value of solubility

    """

    descriptors = molecule.calcdesc(['logP', 'MW', 'atoms'])
    log_p = descriptors['logP']
    mwt = descriptors['MW']
    rb = molecule.OBMol.NumRotors()
    atoms = molecule.atoms
    ap = len([a for a in atoms if a.OBAtom.IsAromatic()])/descriptors['atoms']

    log_sw = 0.16 - 0.62 * log_p - 0.0062 * mwt + 0.066 * rb - 0.74 * ap
    if log_value:
        return log_sw
    else:
        return np.exp(log_sw)


def molecule_convex_hull_volume(molecule, forcefield='mmff94', steps=100):
    """
    Calculates the volume of the convex hull formed by the molecule.

    Arguments
    ---------
    molecule: pybel.Molecule
    """
    assert isinstance(molecule, pybel.Molecule)
    assert forcefield in pybel.forcefields
    molecule.addh()
    molecule.make3D(forcefield=forcefield, steps=steps)

    xyz = [a.coords for a in molecule.atoms]
    return convex_hull_volume(xyz)


def monte_carlo_volume(molecule, coords=None, tolerance=0.01, max_iterations=10000,
                       step_size=1000, seed=time.time(), verbose=False):
    """
    Adapted from:

    Simple Monte Carlo estimation of VdW molecular volume (in A^3)
    by Geoffrey Hutchison <geoffh@pitt.edu>

    https://github.com/ghutchis/hutchison-cluster

    Arguments
    ---------
    molecule: pybel.Molecule
        A molecule from pybel.
    coords: list
        A list of pre selected x,y,z coords. It must match the atoms order.
    tolerance: float
        The tolerance for convergence of the monte carlo abs(new_volume - volume) < tolerance
    max_iterations: int
        Number of iterations before the algorithm starts
    step_size: int
        Number of points to add each step.
    seed: object
        A valid seed for random.
    verbose: bool
        Print debug information if True.

    Returns
    -------
    float
        Molecule volume

    """

    assert isinstance(molecule, pybel.Molecule)
    if coords is None:
        coords = np.array([a.coords for a in molecule.atoms], dtype=np.float32)
    vdw_radii = np.array([pybel.ob.etab.GetVdwRad(a.atomicnum) for a in molecule.atoms], dtype=np.float32)
    return mc_vol(coords, vdw_radii, tolerance, max_iterations, step_size, seed, int(verbose))