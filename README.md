
# Sourcemap Extractor

Simple extractor for uncompiled, uncompressed SPA code from webpack sourcemaps ⚙️. The original purpose of sourcemap is to make debugging minified JavaScript code more easier. But with the sourcemap being enable, we can extract or just see the original code not to mention the logical part, api endpoints, comments, hidden functionally (for those website that differ between admin and normal user), and many interesting stuff. So for security perspective, this  extractor is to show that how unsafe a production website with sourcemap enable can be.



## Acknowledgments 📄

The original code is from [unwebpack-sourcemap](https://github.com/rarecoil/unwebpack-sourcemap). So give it look to the original repo.



## Getting Started 🛠

These instructions will get you a copy of the project up and running on your local machine. I suggest using python 3 as some library is for python 3 only. 

### Prerequisites

Go to project directory and install all dependencies

```shell
pip install -r dependencies.txt
```

### Flags

Flag list:

- `--local` for local sourcemap
- `--detect` detect the source for remote sourcemap

### Extract from local sourcemaps

```
python3 main.py --local <path_to_sourcemap> <output_dir_name>
```

The args `--local` indicate that the sourcemap is in local machine. `<output_dir_name>` is the directory where the result will be put.

### Extract from remote sourcemaps

```
python3 main.py <path_to_remote_sourcemap> <output_dir_name>
```

For remote sourcemap, it is not necessary to put the flag `--local`

### Extract from remote SPA root

```
python3 main.py --detect <path_to_remote_spa_root> <output_dir_name>
```

If you do not know where the source maps is, you can use `--detect` provided with SPA root folder.  It will attempt to read all `<script src>` on an HTML page, fetch JS assets, look for `sourceMappingURI`, and pull sourcemaps from remote sources



## Future Plan ⏱

I don't know if it is possible but I plan to implement below list.

- [ ] CSS extractor
- [ ] Image/Assets extractor