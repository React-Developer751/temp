/** Translate a small glob (`*`, `**`, `?`) to a RegExp that matches a whole "/"-separated path. */
export function globToRegExp(glob) {
  let re = '';
  for (let k = 0; k < glob.length; k++) {
    const c = glob[k];
    if (c === '*') {
      if (glob[k + 1] === '*') {
        k++;
        if (glob[k + 1] === '/') { k++; re += '(?:.*/)?'; } else re += '.*';
      } else re += '[^/]*';
    } else if (c === '?') re += '[^/]';
    else re += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  }
  return new RegExp(`^${re}$`);
}
