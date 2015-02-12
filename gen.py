#!/usr/bin/env python3
import sys, os, textwrap, subprocess, io, hashlib, tarfile, shutil
from os import path

fbuild = sys.argv[1]
bbase = path.join('bin', 'fbuild')
lbase = path.join('lib', 'fbuild')
bin = path.realpath(path.join(fbuild, bbase))
lib = path.realpath(path.join(fbuild, lbase))
ver = subprocess.check_output([bin, '--version']).strip()

def tar_add_mem(t, p, d):
    i = tarfile.TarInfo(p)
    d = d.encode('utf-8')
    i.size = len(d)
    t.addfile(i, io.BytesIO(d))

b = io.BytesIO()
with tarfile.open(mode='w:gz', fileobj=b) as tar:
    tar.add(lib, lbase, exclude=lambda p: path.splitext(p)[0] == '.py')
    #for root, dirs, files in os.walk(lib):
    #    for file in files:
    #        if path.splitext(file)[1] != '.py': continue
    #        p = path.join(root, file)
    #        assert p.startswith(lib)
    #        tar.add(p, path.join(lbase, p[len(lib)+1:]))
    tar.add(bin, bbase)
    hash = hashlib.sha224(b.getvalue()).hexdigest()
    tar_add_mem(tar, 'hash', hash)

with open('pfbuild', 'w') as out:
    out.write(textwrap.dedent('''
    #!/usr/bin/env python3
    import sys, io, os.path, tarfile

    do_update = True
    if os.path.exists(os.path.join('_fbuild', 'hash')):
        with open(os.path.join('_fbuild', 'hash'), 'r') as h:
            if h.read().strip() == '%s':
                do_update = False
    else:
        os.mkdir('_fbuild')

    if do_update:
        zdata = io.BytesIO(%s)
        tarfile.open(mode='r:gz', fileobj=zdata).extractall('_fbuild')

    os.environ['PYTHONPATH'] = os.pathsep.join(sys.path)+os.pathsep+os.path.join('_fbuild', 'lib')

    os.execl(sys.executable, sys.executable, os.path.join('_fbuild', 'bin', 'fbuild'), *sys.argv[1:])
    ''' % (hash, repr(b.getvalue()))).strip())

os.chmod('pfbuild', 511)
