#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_data import install_data
import glob, os, sys
from distutils.dep_util import newer
from distutils.log import info

PO_DIR="po"

class InstallData(install_data):

    def run(self):
        self.data_files.extend(self._compile_po_files())

        install_data.run(self)

    def _compile_po_files(self):

        data_files = []

        if sys.platform == "win32":
            return data_files

        for po in glob.glob(os.path.join(PO_DIR, "*.po")):
            lang = os.path.basename(po[:-3])
            mo = os.path.join('build', 'mo', lang, 'lum.mo')

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                info("Creating %s" % directory)

                os.makedirs(directory)

            if newer(po, mo):
                cmd = "msgfmt -o %s %s" % (mo, po)
                info("Compiling %s -> %s" % (po, mo))
                if os.system(cmd) != 0:
                    raise SystemExit("Error while running msgftm")

                dest = os.path.dirname(os.path.join('share', 'locale',
                                                    lang, 'LC_MESSAGES',
                                                    'lum.mo'))

                data_files.append((dest, [mo]))

        return data_files


setup(name='Lum',
      version='0.1',
      description='Ldap User Manager',
      author='Leonardo Robol',
      author_email='robol@poisson.phc.unipi.it',
      url='http://poisson.phc.unipi.it/~robol/wordpress/programmi/lum/',
      packages=['lum', 'lum.interface'],
      package_dir = { 'lum': 'src/lum', 'lum.interface': 'src/lum/interface' },
      scripts = ['lum'],
      package_data = {'lum.interface': ['ui/*.ui', 'ui/*.png']},
      data_files = [('share/applications', ['data/lum.desktop']),
                    ('share/pixmaps', ['data/lum.svg'])],
      cmdclass={'install_data': InstallData},
     )
