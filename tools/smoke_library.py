#!/usr/bin/env python3
"""Optional browser checks. Serve dist/ first; requires Playwright and Chromium.

python3 tools/smoke_library.py --base-url http://localhost:8000/
"""
import argparse
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8000/')
    parser.add_argument('--screenshots', type=Path)
    args=parser.parse_args()
    base=args.base_url.rstrip('/')+'/'
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror', lambda error: errors.append(str(error)))
        def visit(path, selector='h1'):
            page.goto(base+path)
            page.wait_for_selector(selector)
        visit('#library','#libraryQ')
        page.select_option('#libraryCollection','Vatican II')
        assert page.locator('#libraryList .source-card').count()==16
        page.fill('#libraryQ','Gravissimum')
        assert page.locator('#libraryList .source-card').count()==1
        assert 'External full text only' in page.locator('#libraryList').inner_text()
        page.fill('#libraryQ','')
        if args.screenshots:
            args.screenshots.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(args.screenshots/'source-library-desktop.png'))
        visit('#source-lg','.source-details')
        assert 'Selected excerpts' in page.locator('.era-head').inner_text()
        assert '69 numbered sections' in page.locator('.era-head').inner_text()
        assert page.locator('.era-head a:has-text("Official full text")').count()==1
        visit('#doc-DCE','#libraryList')
        assert page.locator('#libraryList .source-card').count()==2
        assert 'Dominicae Cenae' in page.locator('#libraryList').inner_text()
        assert 'Deus Caritas Est' in page.locator('#libraryList').inner_text()
        for query, count in [('document:"Mediator Dei"',4),('document:"Deus Caritas Est"',5),('document:"Dominicae Cenae"',1)]:
            visit('?q='+quote(query),'.res-head')
            assert page.locator('.hit').count()==count,query
        for query in ['document:"Christus Dominus"','"Sacramentum Caritatis"']:
            visit('?q='+quote(query),'.res-head')
            assert page.locator('.hit').count()==0
            assert page.locator('.search-sources .source-card').count()==1
        visit('?q=unfindablezzzz','#saveResearchGap')
        assert page.evaluate("localStorage.getItem('dz-research-gaps')") is None
        page.click('#saveResearchGap')
        visit('#coverage','[data-gap-remove]')
        assert page.locator('[data-gap-search]').count()==1
        assert 'research=unfindablezzzz' in page.locator('a:has-text("Open a proposal")').get_attribute('href')
        page.click('[data-gap-search]')
        page.wait_for_selector('#saveResearchGap')
        assert page.locator('#q').input_value()=='unfindablezzzz'
        visit('#coverage','[data-gap-remove]')
        page.click('[data-gap-remove]')
        assert page.locator('[data-gap-remove]').count()==0
        visit('#nRDOS','#nRDOS .source-relations')
        assert page.locator('#nRDOS .source-relation').count()==2
        visit('n/1839/')
        assert page.locator('details:has-text("Editorial relationship")').count()==2
        visit('#thread-orders')
        assert page.locator('h1').inner_text()!='Sources of Catholic Dogma'
        visit('#source-mediator-dei','.source-details')
        page.click('#n2297 [data-latin]')
        page.wait_for_selector('#n2297 .latin', timeout=15000)
        page.set_viewport_size({'width':390,'height':844})
        for path in ['#library','#coverage','#source-lg','#thread-orders']:
            visit(path)
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'),path
        visit('#library','#libraryQ')
        page.fill('#libraryQ','')
        page.select_option('#libraryCollection','Vatican II')
        if args.screenshots:page.screenshot(path=str(args.screenshots/'source-library-mobile.png'))
        assert not errors,errors
        browser.close()
    print('Browser checks passed: catalogue, document collisions, source search, feedback, relationships, Latin and mobile layout.')


if __name__=='__main__':main()
