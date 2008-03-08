#!/usr/bin/env python
import sys
import os
import os.path





freetype2_sources =['autohint/autohint.c',
                    'base/ftbase.c','base/ftsystem.c','base/ftinit.c',
                    'base/ftglyph.c','base/ftmm.c','base/ftbdf.c',
                    'base/ftbbox.c','base/ftdebug.c','base/ftxf86.c',
                    'base/fttype1.c','bdf/bdf.c',
                    'cff/cff.c',
                    'cid/type1cid.c',
                    'pcf/pcf.c','pfr/pfr.c',
                    'psaux/psaux.c',
                    'pshinter/pshinter.c',
                    'psnames/psnames.c',
                    'raster/raster.c',
                    'sfnt/sfnt.c',
                    'smooth/smooth.c',
                    'truetype/truetype.c',
                    'type1/type1.c',
                    'type42/type42.c',
                    'winfonts/winfnt.c',
                    'gzip/ftgzip.c',
                    'base/ftmac.c',
                    ]

freetype2_dirs = [
    'base','bdf','cache','cff','cid','pcf','pfr',
    'psaux','pshinter','psnames','raster','sfnt',
    'smooth','truetype','type1','type42','winfonts',
    'gzip'
    ]



def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    from numpy.distutils.system_info import dict_append, get_info

    agg_dir = 'agg-24'
    agg_lib = 'agg24_src'

    config = Configuration('agg',parent_package,top_path)
    numerix_info = get_info('numerix')

    if ('NUMPY',None) in numerix_info.get('define_macros',[]):
        dict_append(numerix_info,
                    define_macros = [('PY_ARRAY_TYPES_PREFIX','NUMPY_CXX'),
                                     ('OWN_DIMENSIONS','0'),
                                     ('OWN_STRIDES','0')])
    if sys.platform=='win32':
        plat = 'win32'
    elif sys.platform == 'darwin':
        plat = 'gl'
    else:
        #plat = 'gtk1'  # use with gtk1, it's fast
        plat = 'x11'  # use with gtk2, it's slow but reliable
        #plat = 'gdkpixbuf2'

    # freetype2_src library:
    prefix = config.paths('freetype2/src')[0]

    def get_ft2_sources((lib_name, build_info), build_dir):
        sources = [prefix + "/" + s for s in freetype2_sources]
        if sys.platform=='darwin':
            return sources[:]
        return sources[:-1]

    ft2_incl_dirs = ['freetype2/src/' + s for s in freetype2_dirs] \
                    + ['freetype2/include', 'freetype2/src']
    ft2_incl_dirs = config.paths(*ft2_incl_dirs)
    if sys.platform == 'darwin':
        ft2_incl_dirs.append("/Developer/Headers/FlatCarbon")

    config.add_library('freetype2_src',
                       sources = [get_ft2_sources],
                       include_dirs = ft2_incl_dirs,
                       depends = ['freetype2']
                       )


    agg_include_dirs = [agg_dir+'/include',agg_dir+'/font_freetype'] + ft2_incl_dirs
    freetype_lib = 'freetype2_src'


    agg_sources = [agg_dir+'/src/*.cpp',
                    agg_dir+'/font_freetype/*.cpp']
    config.add_library(agg_lib,
                       agg_sources,
                       include_dirs = agg_include_dirs,
                       depends = [agg_dir])

    kiva_include_dirs = ['src'] + agg_include_dirs
    config.add_library('kiva_src',
                       ['src/kiva_*.cpp'],
                       include_dirs = kiva_include_dirs,
                       )

    if sys.platform == 'darwin':
        define_macros = [('__DARWIN__', None)]
        extra_link_args = ['-framework', 'Carbon']
    else:
        define_macros = []
        extra_link_args = []

    # MSVC6.0: uncomment to handle template parameters:
    #extra_compile_args = ['/Zm1000']
    extra_compile_args = []

    # XXX: test whether numpy has weakref support

    build_info = {}

    dict_append(build_info,
                sources = ['agg.i'],
                include_dirs = kiva_include_dirs,
                libraries = ['kiva_src', agg_lib, freetype_lib],
                depends = ['src/*.[ih]'],
                extra_compile_args = extra_compile_args,
                extra_link_args = extra_link_args,
                define_macros=define_macros,
                )
    dict_append(build_info, **numerix_info)
    config.add_extension('_agg', **build_info)

    sources = [os.path.join('src',plat,'plat_support.i'),
               os.path.join('src',plat,'agg_bmp.cpp'),
               ]
    if plat != 'gl':
        sources.append(os.path.join('src',plat,'agg_platform_specific.cpp'))

    plat_info = {}
    dict_append(plat_info, libraries = [agg_lib],
                include_dirs = kiva_include_dirs,
                extra_compile_args = extra_compile_args,
                depends = ['src'])
    dict_append(plat_info, **numerix_info)

    if plat=='win32':
        dict_append(plat_info, libraries = ['gdi32','user32'])
    elif plat in ['x11','gtk1']:
        x11_info = get_info('x11',notfound_action=1)
        print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        print x11_info
        dict_append(plat_info,**x11_info)
    elif plat=='gdkpixbuf2':
        #gdk_pixbuf_xlib_2 = get_info('gdk_pixbuf_xlib_2',notfound_action=1)
        #dict_append(plat_info,**gdk_pixbuf_xlib_2)
        gtk_info = get_info('gtk+-2.0')
        dict_append(plat_info,**gtk_info)
        #x11_info = get_info('x11',notfound_action=1)
        #dict_append(plat_info,**x11_info)
    elif plat == 'gl':
        if sys.platform == 'darwin':
            dict_append(plat_info, include_dirs = \
                        ['/System/Library/Frameworks/%s.framework/Versions/A/Headers'%x
                         for x in ['Carbon', 'ApplicationServices', 'OpenGL']],
                        define_macros = [('__DARWIN__',None)],
                        extra_link_args = \
                        ['-framework %s' % x
                         for x in ['Carbon', 'ApplicationServices', 'OpenGL']]
                        )
        else:
            msg = "OpenGL build support only on MacOSX right now. Help me!"
            raise NotImplementedError, msg


    config.add_extension('_plat_support',
                         sources,
                         **plat_info
                         )

    config.add_data_dir('docs')
    config.add_data_dir('tests')
    config.add_data_files('*.txt','*.bat')

    return config
