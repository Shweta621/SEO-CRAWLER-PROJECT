
from gzip import GzipFile
import logging
from concurrent import futures
from xml.etree import ElementTree
from urllib.request import urlopen, Request

from advertools import __version__ as version
import pandas as pd

logging.basicConfig(level=logging.INFO)

headers = {'User-Agent': 'advertools-' + version}


def _sitemaps_from_robotstxt(robots_url):
    sitemaps = []
    robots_page = urlopen(Request(robots_url, headers=headers))
    for line in robots_page.readlines():
        line_split = [s.strip() for s in line.decode().split(':', maxsplit=1)]
        if line_split[0].lower() == 'sitemap':
            sitemaps.append(line_split[1])
    return sitemaps


def sitemap_to_df(sitemap_url, max_workers=8, recursive=True):
    if sitemap_url.endswith('robots.txt'):
        return pd.concat([sitemap_to_df(sitemap, recursive=recursive)
                          for sitemap in _sitemaps_from_robotstxt(sitemap_url)],
                         ignore_index=True)
    if sitemap_url.endswith('xml.gz'):
        xml_text = urlopen(Request(sitemap_url,
                                   headers={'Accept-Encoding': 'gzip',
                                            'User-Agent': 'advertools-' +
                                                          version}))
        resp_headers = xml_text.getheaders()
        xml_text = GzipFile(fileobj=xml_text)
    else:
        xml_text = urlopen(Request(sitemap_url, headers=headers))
        resp_headers = xml_text.getheaders()
    xml_string = xml_text.read()
    root = ElementTree.fromstring(xml_string)

    sitemap_df = pd.DataFrame()

    if (root.tag.split('}')[-1] == 'sitemapindex') and recursive:
        multi_sitemap_df = pd.DataFrame()
        sitemap_url_list = []
        for elem in root:
            for el in elem:
                if 'loc' in el.tag:
                    if el.text == sitemap_url:
                        error_df = pd.DataFrame({
                            'sitemap': [sitemap_url],
                            'errors': ['WARNING: Sitemap contains a link to itself']
                        })
                        multi_sitemap_df = multi_sitemap_df.append(error_df,
                                                                   ignore_index=True)
                    else:
                        sitemap_url_list.append(el.text)
        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            to_do = []
            for sitemap in sitemap_url_list:
                future = executor.submit(sitemap_to_df, sitemap)
                to_do.append(future)
            done_iter = futures.as_completed(to_do)
            for future in done_iter:
                try:
                    multi_sitemap_df = multi_sitemap_df.append(future.result(),
                                                               ignore_index=True)
                except Exception as e:
                    error_df = pd.DataFrame(dict(errors=str(e)),
                                            index=range(1))
                    future_str = hex(id(future))
                    hexes = [hex(id(f)) for f in to_do]
                    index = hexes.index(future_str)
                    error_df['sitemap'] = sitemap_url_list[index]
                    logging.warning(msg=str(e) + ' ' + sitemap_url_list[index])
                    multi_sitemap_df = multi_sitemap_df.append(error_df,
                                                               ignore_index=True)
        return multi_sitemap_df

    else:
        logging.info(msg='Getting ' + sitemap_url)
        elem_df = _parse_sitemap(root)
        sitemap_df = sitemap_df.append(elem_df, ignore_index=True)
        sitemap_df['sitemap'] = [sitemap_url] if sitemap_df.empty else sitemap_url
    if 'lastmod' in sitemap_df:
        try:
            sitemap_df['lastmod'] = pd.to_datetime(sitemap_df['lastmod'], utc=True)
        except Exception as e:
            pass
    if 'priority' in sitemap_df:
        try:
            sitemap_df['priority'] = sitemap_df['priority'].astype(float)
        except Exception as e:
            pass
    etag_lastmod = {header.lower().replace('-', '_'): val.replace('"', '')
                    for header, val in resp_headers
                    if header.lower() in ['etag', 'last-modified']}
    sitemap_df = sitemap_df.assign(**etag_lastmod)
    if 'last_modified' in sitemap_df:
        sitemap_df['sitemap_last_modified'] = pd.to_datetime(sitemap_df['last_modified'])
        del sitemap_df['last_modified']
    sitemap_df['sitemap_size_mb'] = len(xml_string) / 1024 / 1024
    sitemap_df['download_date'] = pd.Timestamp.now(tz='UTC')
    return sitemap_df
