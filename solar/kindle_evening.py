"""The Evening Edition: a short bedtime read for the Kindle, a sibling of the Morning Edition.

Cover, the day's three biggest stories, one from close to home, tomorrow's weather, tonight's
sky, a poem and a quiet close: about nine pages, five or six minutes. It uses the Morning
Edition's type, chrome, pager and Sections navigator (solar/kindle_full.py), with no pictures
and no section fronts.

Story summaries come from web/evening.json, written each evening by the local model on
Parker's PC (local/refresh_lists.py, list "evening"). Without a fresh one, the feed summaries
are used instead. The editorial rules (what goes in, the order, the tone) came from a
sleep-psychology review: close the day's loops, end calm, never a reason to stay up late.

    python -m solar.kindle_evening data/dashboard.json web/evening.json _site
"""
import datetime as dt
import html
import json
import math
import os
import re
import sys

from . import bedtime_poems, engraving, evening
try:  # the engravers' optional pieces: every page renders without them
    from . import engraving_thai
except Exception:  # noqa: BLE001
    engraving_thai = None
try:
    from .engraving_vignettes import VIGNETTES
except Exception:  # noqa: BLE001
    VIGNETTES = {}
try:
    from . import engraving_medallions
except Exception:  # noqa: BLE001
    engraving_medallions = None
try:
    from . import engraving_panorama
except Exception:  # noqa: BLE001
    engraving_panorama = None
from .kindle_full import EINK_CSS, page, self_host_fonts, _JUMP, _TITLES, BUILD

TZ = evening.TZ
E = html.escape

EVENING_CSS = r"""
/* ===== The Evening Edition: the Morning Edition's quieter sibling, engraved ===== */
/* Line weights 0.6 / 1 / 1.6 px; tones are SVG hatch and stipple patterns (ORNAMENTS["defs"]), never solid grey. */
html.kev body .krun{border-bottom:3px double #000 !important}
html.kev.kpaged .kbar{border-top:3px double #000}
html.kev .krun .krunh{padding-left:0 !important}
#kmain svg text{font-family:var(--k-serif);fill:#000}
html.kev #kmain svg text.ksm{font:italic 700 8.4px var(--k-serif) !important;stroke-width:0 !important}
html.kev #kmain svg text.kribt{font:italic 600 10px var(--k-serif) !important;stroke-width:0 !important}
html.kev .kcontents #kmain .kribbon{margin:4px auto 0}
html.kev .kcontents #kmain .kribbon+.kevrest{border-top:0 !important;padding-top:4px !important}
html.kev #kmain svg text.kmicro{font:600 4.4px var(--k-serif) !important;stroke-width:0 !important;letter-spacing:.06em}
#kmain .kegg{position:absolute !important;right:66px;bottom:26px}
#kmain svg.kfr path,#kmain svg.kfr circle{vector-effect:non-scaling-stroke}
#kmain .kfill{display:block;height:0;overflow:hidden;position:relative}
#kmain .kfill svg.kfr,#kmain .kfill svg.kfp{display:none !important}
#kmain .kfill{-webkit-flex:none;flex:none;display:-webkit-flex;display:flex;-webkit-flex-direction:column;flex-direction:column;-webkit-justify-content:space-evenly;justify-content:space-evenly}
#kmain .kplate1{display:block;line-height:0;margin:0 auto;text-align:center}#kmain svg.kpv{display:none;margin:0 auto;max-width:100%}
#kmain .kfi{display:none;flex:none;margin:0;text-align:center;line-height:0}
#kmain .kfi svg{display:inline-block;max-width:100%;vertical-align:top}
#kmain .kfi.kfrow{-webkit-justify-content:center;justify-content:center;-webkit-align-items:center;align-items:center}#kmain .kfrow svg{margin:0 4px;-webkit-flex:0 1 auto;flex:0 1 auto;min-width:0}
html.kev #kmain svg text.kseal{font:700 17px var(--k-serif) !important;stroke-width:0 !important}
html.kev #kmain svg text.ksealno{font:italic 600 7.4px var(--k-serif) !important;stroke-width:0 !important}
#kmain .korn{display:block;margin:0 auto;overflow:visible;max-width:100%}
#kmain .kdefs{position:absolute;left:0;top:0;width:0;height:0;overflow:hidden}
/* the border family: cover, poem plate and close */
#kmain .kframe{position:relative;padding:22px 24px 20px !important;margin:0 !important}
#kmain .kfs{position:absolute;display:block;overflow:hidden;margin:0}
#kmain .kfs-t{left:0;top:0;width:100%;height:14px}
#kmain .kfs-b{left:0;bottom:0;width:100%;height:14px;-webkit-transform:scaleY(-1) !important;transform:scaleY(-1) !important}
#kmain .kfs-l{left:0;top:0;width:14px;height:100%}
#kmain .kfs-r{right:0;top:0;width:14px;height:100%;-webkit-transform:scaleX(-1) !important;transform:scaleX(-1) !important}
#kmain .kround{position:absolute;margin:0 !important}
#kmain .kround-tl{left:0;top:0}#kmain .kround-tr{right:0;top:0}#kmain .kround-bl{left:0;bottom:0}#kmain .kround-br{right:0;bottom:0}
/* the cover */
html.kev .kcontents #kmain .kmast{text-align:center;padding:0 !important;margin:0 !important}
html.kev .kcontents #kmain .kcartouche{margin:0 auto 2px}
html.kev .kcontents #kmain .kname{font:italic 700 44px/48px var(--k-serif) !important;letter-spacing:-.012em;margin:0 0 6px !important}
html.kev .kcontents #kmain .kdate{display:flex;align-items:center;justify-content:center;border:0 !important;padding:0 !important;margin:7px 0 0 !important;
  font:600 12px/16px var(--k-serif) !important;letter-spacing:.15em;text-transform:uppercase;white-space:nowrap}
html.kev .kcontents #kmain .kdate .korn{display:inline-block;margin:0 10px;flex:none}
html.kev .kcontents #kmain .kcentre{margin:9px auto 8px}
html.kev .kcontents #kmain .kgl{display:flex;align-items:center;border-top:1px solid #000;border-bottom:1px solid #000;padding:8px 0 !important;margin:0 0 10px !important}
html.kev .kcontents #kmain .kgl .kdeg{flex:none;width:auto;min-width:118px;display:block;font:700 54px/50px var(--k-serif);letter-spacing:-.02em;margin:0 !important;text-align:left}
html.kev .kcontents #kmain .kgl .kdeg .ktmr{display:block;font:600 12px/15px var(--k-serif);letter-spacing:.15em;text-transform:uppercase;margin:0 0 2px}
html.kev .kcontents #kmain .kgl .kdeg small{display:block !important;margin:4px 0 0 !important;white-space:nowrap;font:italic 430 14px/18px var(--k-serif) !important;
  text-transform:none !important;letter-spacing:0 !important}
html.kev .kcontents #kmain .kgl .kwx{flex:1 1 auto;min-width:0;margin:0 0 0 18px !important;padding:0 0 0 18px !important;border-left:1px solid var(--hair);
  font:italic 430 20px/26px var(--k-serif) !important;text-align:left}
html.kev .kcontents #kmain .klab{display:flex;align-items:center;border:0 !important;padding:0 !important;margin:0 0 2px !important;
  font:600 12px/16px var(--k-serif) !important;letter-spacing:.18em;text-transform:uppercase}
html.kev .kcontents #kmain .klab:before,html.kev .kcontents #kmain .klab:after{content:"";flex:1 1 auto;border-top:1px solid #000;margin:0 12px}
html.kev .kcontents #kmain .kleads a{display:flex;align-items:baseline;padding:6px 0 7px !important;border-bottom:1px solid var(--hair);text-align:left}
html.kev .kcontents #kmain .kleads a:last-child{border-bottom:0}
html.kev .kcontents #kmain .kleads b{display:-webkit-box !important;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}
html.kev .kcontents #kmain .ktight .kcentre{width:400px;height:auto;margin:6px auto 4px}
html.kev .kcontents #kmain .ktight .kgl{padding:5px 0 !important;margin-bottom:6px !important}
html.kev .kcontents #kmain .ktight .kgl .kdeg{font-size:46px;line-height:44px}
html.kev .kcontents #kmain .ktight .kgl .kwx{font-size:18px !important;line-height:23px !important}
html.kev .kcontents #kmain .ktight .kleads a{padding:4px 0 5px !important}
html.kev .kcontents #kmain .kleads i{flex:none;width:34px;font:600 12px/16px var(--k-serif);font-style:normal;letter-spacing:.12em}
html.kev .kcontents #kmain .kleads b,html.kev .kcontents #kmain .kleads a:first-child b{flex:1 1 auto;min-width:0;font:680 18px/23px var(--k-serif) !important}
html.kev #kmain .kevrest{text-align:center;font:italic 430 14px/19px var(--k-serif) !important;color:#000 !important;
  border-top:1px solid #000;padding:7px 0 0 !important;margin:2px 0 0 !important}
html.kev .kcontents #kmain .kresume{display:flex;align-items:baseline;border:0 !important;border-top:1px solid #000 !important;border-bottom:1px solid #000 !important;
  padding:5px 2px !important;margin:8px 0 0 !important;text-align:left}
html.kev .kcontents #kmain .kresume small{flex:none;display:inline;font:600 11px/16px var(--k-serif) !important;letter-spacing:.14em;margin-right:10px}
html.kev .kcontents #kmain .kresume b{flex:1 1 auto;min-width:0;font:italic 680 15px/20px var(--k-serif) !important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
html.kev .kcontents #kmain .knonews{text-align:center;font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important;margin:4px 0 10px !important}
html.kev #kmain .kcolo{text-align:center;font:600 12px/15px var(--k-serif) !important;letter-spacing:.24em;text-transform:uppercase;margin:3px 0 0 !important}
/* story pages: clean text, ornament at the head and tail */
#kmain .khv{margin:0 0 6px}
#kmain .khv svg.kvig{width:auto;height:46px}
#kmain .khv svg.kvig2{width:84px !important;height:56px !important}
#kmain .khv svg.khp{display:block;width:100% !important;height:56px !important;margin:0 auto}
#kmain h2.khed{font:700 var(--t2)/var(--l2) var(--k-serif) !important;letter-spacing:-.01em;margin:0 0 var(--s2) !important}
#kmain .kbody p{margin:0 0 var(--s2) !important}
#kmain .kbody p.kdrop:first-letter{float:left;font:700 60px/50px var(--k-serif);margin:3px 7px 0 -1px;padding:0}
#kmain .kbody p.kdrop3:first-letter{font-size:84px;line-height:70px;margin-top:4px}
#kmain .kast{margin:0 auto var(--s2)}
#kmain .kdiv{margin:var(--s2) auto 6px}
#kmain .knextstep{border-top:0 !important;padding-top:0 !important;margin:0 0 var(--s2) !important}
#kmain .knextstep b,#kmain .kwarn b,#kmain .ksky b,#kmain .kmoon b{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase}
#kmain .ksources{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;color:var(--ink2) !important;margin:0 !important}
#kmain .kover{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;border-top:1px solid #000;padding-top:var(--s2) !important;margin-top:var(--s2) !important}
#kmain .ktail{margin:var(--s3) auto 0}
/* every text page: the light frame, the head band, inlaid boxes, engraved drop caps */
#kmain .kframe.klite{padding:15px 20px 14px !important}
#kmain .kls-t{left:0;top:0;width:100%;height:9px}
#kmain .kls-b{left:0;bottom:0;width:100%;height:9px;-webkit-transform:scaleY(-1) !important;transform:scaleY(-1) !important}
#kmain .kls-l{left:0;top:0;width:9px;height:100%}
#kmain .kls-r{right:0;top:0;width:9px;height:100%;-webkit-transform:scaleX(-1) !important;transform:scaleX(-1) !important}
#kmain svg.khb{width:100%;height:auto;margin:0 0 8px}
html.kev #kmain svg text.khb{font:600 12px var(--k-serif) !important;letter-spacing:.16em;text-transform:uppercase;stroke-width:0 !important}
#kmain .kbox{position:relative;padding:4px 0 0 !important;margin:var(--s1) 0 var(--s1) !important;border-top:1px solid #000}
#kmain .kbox.ksrc{padding:3px 0 0 !important;margin-bottom:0 !important;border-top:.5px solid #000}
#kmain .kbox svg.kfs{display:none !important}
#kmain .kbox p{margin:0 !important}
#kmain .kbox .kover{border-top:1px solid var(--hair);padding-top:3px !important;margin-top:4px !important}
#kmain .kbx-t{left:0;top:0;width:100%;height:6px}
#kmain .kbx-b{left:0;bottom:0;width:100%;height:6px}
#kmain .kbx-l{left:0;top:0;width:6px;height:100%}
#kmain .kbx-r{right:0;top:0;width:6px;height:100%}
#kmain .kbody p.kdrop:first-letter{border:3px double #000;padding:4px 7px 0 !important;margin:2px 9px 0 0 !important;
  background:#fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='4'%3E%3Ccircle cx='1' cy='1' r='.45'/%3E%3Ccircle cx='3' cy='3' r='.45'/%3E%3C/svg%3E")}
#kmain .kbody p.kdrop3:first-letter{padding:6px 9px 2px !important}
#kmain .kmed{position:absolute;margin:0 !important;top:13%;margin-top:-16px !important}
#kmain .kmed-l{left:-9px}#kmain .kmed-r{right:-9px}
/* tomorrow: an almanac entry */
#kmain .kalm{display:flex;align-items:center;border-top:3px double #000;border-bottom:1px solid #000;padding:10px 0 !important;margin:0 0 var(--s2) !important}
#kmain .kalm .kvwx{flex:none;width:156px;height:auto;margin:0 22px 0 0}
#kmain .kalm-t{flex:1 1 auto;min-width:0}
#kmain .kalm .kdeg{font:700 60px/58px var(--k-serif);letter-spacing:-.02em}
#kmain .kalm small{display:block;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;margin:2px 0 6px}
#kmain .kalm-lead{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important;margin:0 !important}
#kmain .ksun3{display:flex;border-bottom:1px solid #000;margin:0 0 var(--s2) !important}
#kmain .ksun3>div{flex:1 1 0;text-align:center;padding:5px 0 7px}
#kmain .ksun3>div+div{border-left:1px solid var(--hair)}
#kmain .ksun3 .k{display:block;font:600 12px/16px var(--k-serif);letter-spacing:.14em;text-transform:uppercase}
#kmain .ksun3 b{display:block;font:700 22px/28px var(--k-serif);font-variant-numeric:tabular-nums}
#kmain .kwarn{border-top:2px solid #000;border-bottom:1px solid #000;padding:var(--s1) 0 !important}
#kmain .kplan,#kmain .kchoice{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important}
#kmain .kchoice{border-top:1px solid #000;padding-top:var(--s2) !important;margin-top:var(--s2) !important}
/* tonight's sky */
#kmain .kmoon{display:flex;align-items:center;margin:0 0 6px !important}
#kmain .kmoon .korn{flex:none;margin:0 18px 0 0}
#kmain .kmoon .kmname{font:italic 430 var(--t3)/var(--l3) var(--k-serif) !important;margin:0 !important}
#kmain .kmoon p{font:430 var(--t5)/var(--l5) var(--k-serif) !important;margin:2px 0 0 !important}
#kmain .kchart{margin:0 0 var(--s2) !important}
#kmain .kchart .korn{margin:0}
#kmain .kcap{text-align:center;font:italic 430 13px/17px var(--k-serif) !important;margin:3px 0 0 !important}
#kmain ul.ksky{list-style:none !important;padding:0 !important;margin:0 0 var(--s2) !important;border-top:1px solid #000}
#kmain .ksky li{border-bottom:1px solid var(--hair);padding:6px 0 !important;margin:0 !important;font:430 var(--t5)/var(--l5) var(--k-serif) !important}
#kmain .klater{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important;margin:0 0 var(--s2) !important}
/* the poem: a bookplate */
#kmain .kplate{text-align:center}
#kmain .kplate .poem-title{font:700 26px/30px var(--k-serif) !important;margin:6px 0 2px !important}
#kmain .kplate .poem-by{font:600 12px/16px var(--k-serif) !important;letter-spacing:.16em;text-transform:uppercase;margin:0 0 12px !important}
#kmain .kplate .poem-text{display:inline-block;text-align:left;line-height:1.3 !important}
#kmain .poem-text{line-height:1.3 !important}
#kmain .poem-text .gap{height:calc(var(--l4)/2)}
#kmain .kplate .ktail{margin-top:12px}
#kmain .kplate.kframe{padding:24px 26px 18px !important}
#kmain .kplate.klong .poem-text{font-size:16px !important;line-height:1.22 !important}
#kmain .kplate.klong .poem-text .gap{height:9px}
#kmain .kplate.klong .poem-title{font-size:22px !important;line-height:26px !important;margin-top:0 !important}
#kmain .kplate.klong .poem-by{margin-bottom:8px !important}

/* no white page: a fine engraved ground under everything, banknote style; type knocked out in white */
/* a light security tint in the margins only, like the guilloche under a banknote; the text column is clean paper */
html.kev body{background:#fff !important}
html.kev #kmain .kframe{background:#fff !important}
html.kev .kbar,html.kev .krun,html.kev .krun *{background-color:#fff !important}
html.kev,html.kev #kmain{background:transparent !important}
html.kev .kendpage #kmain .kfill,html.kev .kcontents #kmain .kfill{margin:0 26px}

/* margins dressed in engraving: medallion flanks and columns, by reference to the page's filler set */
#kmain .kflank{display:-webkit-flex;display:flex;-webkit-justify-content:center;justify-content:center;-webkit-align-items:center;align-items:center}
#kmain .kflank svg.kmu,#kmain .kflank svg.kvu{flex:none;margin:0 5px}
#kmain .kflank.khv{-webkit-justify-content:space-around;justify-content:space-around}#kmain .kflank svg.korn{margin:0 6px !important;flex:none}
#kmain .kft{margin:var(--s3) auto 0}#kmain .kft .ktail{margin:0 8px !important}
#kmain .kcol{position:absolute;top:150px;bottom:70px;width:48px;overflow:hidden;display:-webkit-flex;display:flex;-webkit-flex-direction:column;flex-direction:column;-webkit-justify-content:space-around;justify-content:space-around;-webkit-align-items:center;align-items:center}
#kmain .kcol svg{flex:none}
#kmain .kastrow{margin:0 0 var(--s2)}#kmain .kastrow svg.kastb{width:200px;height:12px;flex:0 1 auto;min-width:0}
#kmain .kastrow svg.kastr{-webkit-transform:scaleX(-1) !important;transform:scaleX(-1) !important}
#kmain .kmoon .kmoonm,#kmain .kalm .kdegm{flex:none;margin-left:auto}#kmain .kalm .kdegm{float:right;margin:0 0 0 8px}#kmain .kalm .kdegm svg{display:block;margin:0 0 6px}
#kmain .kgcol{display:-webkit-flex;display:flex;-webkit-flex-direction:column;flex-direction:column;-webkit-justify-content:space-around;justify-content:space-around;height:150px;margin:0 14px}
#kmain .kcol-l{left:34px}#kmain .kcol-r{right:34px}
html.kev .kendpage #kmain .kegg{bottom:auto;top:30px;right:72px}
/* the close */
html.kev .kendpage #kmain .kend{text-align:center}
html.kev .kendpage #kmain .kframe{-webkit-box-sizing:border-box;box-sizing:border-box;display:-webkit-flex;display:flex;
  -webkit-flex-direction:column;flex-direction:column;-webkit-justify-content:center;justify-content:center}
html.kev .kendpage #kmain .kend .kgn{width:330px;height:auto}
html.kev .kendpage #kmain .kend .kkick{margin:12px 0 2px !important;letter-spacing:.2em !important}
html.kev .kendpage #kmain .kend .kfname{font:italic 700 40px/46px var(--k-serif) !important;margin:0 !important}
html.kev .kendpage #kmain .kend .kfsub{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important;border-bottom:0 !important;margin:4px 0 0 !important;padding:0 !important}
html.kev .kendpage #kmain .kquiet{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important;margin:0 !important;border:0 !important;padding:0 !important}
html.kev .kendpage #kmain .kend .kdiv{margin:14px auto 10px}
html.kev .kendpage #kmain .kend .ktail{margin-top:14px}
"""

# ---- the art direction (solar/atelier.py) ---------------------------------------------------------
# Two grounds (a light hatched field between plaques, a dark matte inside ornament), one moulding
# (heavy rule, light gap, fine rule) on every plaque, and scrollwork only where its region is known:
# the frame's four bands, the bottom panel, the initial. Nothing is laid under the text and cropped.
from . import atelier as _at

_PLQ = (".kp", "h2.khed", ".kbody", ".ktailbox", ".kalm", ".ksun3", ".kmoon", ".kchart", "ul.ksky", ".klater", ".kplan", ".kchoice", ".kwarn",
        ".kpoem", ".kendtxt", ".kmast", ".kgl", ".kleadbox", ".kevrest", ".kresume", ".knonews", ".kframe>p", ".kframe>h2")
EVENING_CSS += (
    "html.kev,html.kev #kmain,html.kev #kmain .kframe,html.kev #kmain .kplate,html.kev #kmain .kend{background-color:transparent !important}\n"
    "html.kev .kbar,html.kev .krun,html.kev .krun *{background-color:#fff !important}\n"
    "html.kev body .krun{box-shadow:-26px 0 0 #fff,26px 0 0 #fff,0 -30px 0 #fff,-26px -30px 0 #fff,26px -30px 0 #fff !important}\n"
    "html.kev body .kbar{box-shadow:-26px 0 0 #fff,26px 0 0 #fff,0 40px 0 #fff,-26px 40px 0 #fff,26px 40px 0 #fff !important}\n"
    # the frame: one geometry on every page; the old strip-and-roundel frames are gone
    "html.kev body #kmain .kframe.kframe{padding:29px 20px 44px !important;margin:0 !important}\n"
    "html.kev body.kcontents #kmain .kframe.kframe{padding:45px 20px 44px !important}\n"
    "html.kev #kmain svg.kfs,html.kev #kmain .kround,html.kev #kmain svg.kast,html.kev #kmain svg.kdiv,html.kev #kmain svg.ktail,"
    "html.kev #kmain svg.kegg,html.kev #kmain .kmed{display:none !important}\n"
    # the title plaque, set into the top band of the frame
    "html.kev body .ktop{position:absolute;left:33px;top:44px;z-index:2;width:552px;height:36px;margin:0 !important;padding:0 !important;text-align:center;"
    "font:600 14px/34px var(--k-serif) !important;letter-spacing:.14em !important;text-transform:uppercase;white-space:nowrap;overflow:hidden}\n"
    "html.kev body.kcontents #kmain .ktop{left:9px;top:0}\n"
    # plaques
    + ",".join(f"html.kev body #kmain {x}" for x in _PLQ) + "{background-color:#fff !important;box-shadow:" + _at.RINGS + " !important;border:0 !important}\n"
    + ",".join(f"html.kev body #kmain#kmain {x}" for x in _PLQ) + "{margin-top:0 !important;margin-bottom:16px !important}\n"
    # labels, labelled-fact tables and the type scale (nothing under 13 px)
    "html.kev body #kmain .klb{font:600 13px/16px var(--k-serif) !important;letter-spacing:.12em !important;text-transform:uppercase;margin:0 0 3px !important;padding:0 !important;"
    "text-align:left;box-shadow:none !important;background:none !important;border:0 !important}\n"
    "html.kev body #kmain .kp p{margin:0 !important;padding:0 !important;box-shadow:none !important;background:none !important;border:0 !important}\n"
    "html.kev body #kmain .kp h2{font:700 30px/34px var(--k-serif) !important;letter-spacing:-.01em;margin:0 0 4px !important;padding:0 !important;box-shadow:none !important;border:0 !important}\n"
    "html.kev body #kmain .kp .klede{font:430 20px/26px var(--k-serif) !important}html.kev body #kmain .kp .klede2{font:430 22px/28px var(--k-serif) !important}\n"
    "html.kev body #kmain .kp .knote{font:430 15px/20px var(--k-serif) !important}\n"
    "html.kev body #kmain .kp .khr{border-top:1px solid #000 !important;margin-top:6px !important;padding-top:6px !important}\n"
    "html.kev body #kmain table.kt{width:100% !important;border-collapse:collapse !important;table-layout:fixed !important;margin:0 !important;border:0 !important;background:none !important}\n"
    "html.kev body #kmain table.kt th,html.kev body #kmain table.kt td{border:0 !important;background:none !important;text-align:left !important;vertical-align:top !important;"
    "padding:4px 0 !important;font-variant-numeric:tabular-nums}\n"
    "html.kev body #kmain table.kt tr+tr th,html.kev body #kmain table.kt tr+tr td{border-top:1px solid #000 !important}\n"
    "html.kev body #kmain table.kt th{width:96px;font:600 13px/23px var(--k-serif) !important;letter-spacing:.12em !important;text-transform:uppercase}\n"
    "html.kev body #kmain table.kt td{font:430 17px/23px var(--k-serif) !important}\n"
    "html.kev body #kmain table.kt td b{font-weight:700}\n"
    # where-to-look: when / what / where / until
    "html.kev body #kmain table.kt.klook th{width:auto}html.kev body #kmain table.kt.klook th.kw1{width:76px}html.kev body #kmain table.kt.klook th.kw2{width:84px}html.kev body #kmain table.kt.klook th.kw4{width:124px}html.kev body #kmain table.kt.klook td{padding-right:8px !important}\n"
    "html.kev body #kmain table.kt.klook th{line-height:16px !important;padding-top:0 !important}\n"
    "html.kev body #kmain table.kt.klook tr+tr th,html.kev body #kmain table.kt.klook tr+tr td{border-top:1px solid #000 !important}\n"
    # hour by hour
    "html.kev body #kmain table.kt.khours td,html.kev body #kmain table.kt.khours th.kc{text-align:center !important}\n"
    "html.kev body #kmain table.kt.khours th.kc{width:auto}\n"
    "html.kev body #kmain table.kt.khours tr.ktemp td{font:700 22px/28px var(--k-serif) !important}\n"
    "html.kev body #kmain table.kt.khours tr.ksk td{font:430 15px/20px var(--k-serif) !important}\n"
    # the answer: labelled high and low
    "html.kev body #kmain table.kt.kans th,html.kev body #kmain table.kt.kans td{padding:0 !important}\n"
    "html.kev body #kmain table.kt.kans td.khi{width:190px}\n"
    "html.kev body #kmain .khero{display:block;font:700 60px/58px var(--k-serif);letter-spacing:-.02em;font-variant-numeric:tabular-nums}\n"
    "html.kev body #kmain .khero2{display:block;font:700 34px/38px var(--k-serif);font-variant-numeric:tabular-nums}\n"
    "html.kev body #kmain .khero3{display:block;font:700 54px/50px var(--k-serif);letter-spacing:-.02em;font-variant-numeric:tabular-nums}\n"
    "html.kev body #kmain .kalert{font:700 20px/26px var(--k-serif) !important}\n"
    # the cover's lists
    "html.kev body #kmain table.kt.kcv td.kcl{border-left:1px solid #000 !important;padding-left:16px !important;vertical-align:middle !important;font:430 20px/26px var(--k-serif) !important}\n"
    "html.kev body #kmain table.kt.kcv td.khi{width:150px}\n"
    "html.kev body #kmain table.kt.kdaylist th{width:28px;font:430 17px/23px var(--k-serif) !important;letter-spacing:0 !important}\n"
    "html.kev body #kmain table.kt.kdaylist td{font:680 18px/23px var(--k-serif) !important}\n"
    "html.kev body #kmain table.kt.kdaylist td a{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;color:#000;text-decoration:none}\n"
    "html.kev body.kcontents #kmain .kmast .kdate{font:600 13px/16px var(--k-serif) !important;letter-spacing:.12em !important;display:block !important;text-align:center}\n"
    "html.kev body #kmain .ksources{color:#000 !important;font:430 15px/20px var(--k-serif) !important;font-style:normal !important}\n"
    "html.kev body #kmain .kover{font:italic 430 15px/20px var(--k-serif) !important}\n"
    "html.kev body #kmain .kpoem .poem-by{font-size:13px !important}\n"
    "html.kev body #kmain .kpoem .poem-text span{padding-left:1.5em;text-indent:-1.5em}\n"
    "html.kev body #kmain .kplate.klong .poem-text{font-size:18px !important;line-height:1.25 !important}\n"
    "html.kev body #kmain .kchart{padding:4px 12px 6px !important}html.kev body #kmain .kchart svg{display:block;width:100% !important;height:auto !important;margin:0 !important}\n"
    "html.kev body #kmain .kchart .kcap{font:430 15px/20px var(--k-serif) !important;font-style:normal !important;text-align:left !important;margin:4px 0 0 !important}\n"
    "html.kev body .kbar .kprev,html.kev body .kbar .knx{text-transform:none !important;letter-spacing:.02em !important;font:600 16px/20px var(--k-serif) !important}\n"
    + ",".join(f"html.kev body #kmain {x}" for x in _PLQ) + "{padding:7px 12px !important}\n"
    "html.kev body #kmain .kbody p:last-child,html.kev body #kmain .ktailbox p:last-child{margin-bottom:0 !important}\n"
    "html.kev body #kmain .kbody{overflow:hidden}\n"
    "html.kev body #kmain .ktailbox p{margin:0 !important;padding:0 !important;border:0 !important}\n"
    "html.kev body #kmain .ktailbox p+p{border-top:.5px solid #000 !important;margin-top:5px !important;padding-top:4px !important}\n"
    
    "html.kev body #kmain .kmoon{padding:5px 7px !important}html.kev body #kmain .kchart .kcap{margin-top:2px !important}\n"
    # the initial: a plain three-line drop letter in the text face (no engraving under type)
    "html.kev body #kmain .kbody .kini{float:left;font:700 52px/46px var(--k-serif) !important;margin:4px 7px 0 0;padding:0}\n"
    # the cover
    "html.kev body.kcontents #kmain .kmast{padding:4px 7px 6px !important;text-align:center}\n"
    "html.kev body.kcontents #kmain#kmain .kmast .kname{margin:0 !important;box-shadow:none !important}html.kev body.kcontents #kmain .kmast .kdate{margin:2px 0 0 !important}\n"
    "html.kev body #kmain .kcentre{display:block;-webkit-flex:none;flex:none;margin:-3px -6px 10px !important;height:112px}\n"
    "html.kev body #kmain .kcentre .kca{display:none}html.kev body #kmain .kcentre .kca:first-child{display:block}\n"
    "html.kev body #kmain table.kt.kinside td a{color:#000;text-decoration:none}html.kev body #kmain table.kt.kinside td a.khl{font-weight:680}\n"
    "html.kev body #kmain table.kt.kinside th,html.kev body #kmain table.kt.kinside td{padding:3px 0 !important;line-height:22px !important}\n"
    "html.kev body #kmain table.kt.kcv td{padding:0 !important}html.kev body #kmain table.kt.kcv td.kcl{vertical-align:top !important}\n"
    "html.kev body #kmain table.kt.khr{margin-top:6px !important;border-top:1px solid #000 !important}\n"
    "html.kev body.kcontents #kmain .kmast .kdate{overflow:hidden}html.kev body.kcontents #kmain .kmast .kdl{float:left}html.kev body.kcontents #kmain .kmast .kdr{float:right}\n"
    "html.kev body.kcontents #kmain .kcentre{margin:-3px -6px 0 !important}html.kev body.kcontents #kmain .kevrest{margin-bottom:var(--s2) !important}\n"
    "html.kev body.kcontents #kmain .kgl{border:0 !important;padding:4px 7px !important;margin:0 0 var(--s2) !important}\n"
    "html.kev body.kcontents #kmain .kleadbox .klab{margin-top:2px !important}\n"
    "html.kev body #kmain .kevrest{border:0 !important;padding:3px 7px !important;margin:0 !important}\n"
    "html.kev body #kmain .kevrest i{display:block;font-style:italic;font-weight:600}\n"
    "html.kev body #kmain .kcolo{display:none !important}\n"
    # the poem and the close: one plaque each
    "html.kev body #kmain .kpoem{text-align:center;padding:6px 7px 8px !important}\n"
    "html.kev body #kmain .kpoem .poem-title,html.kev body #kmain .kpoem .poem-by{display:block}\n"
    "html.kev body #kmain .kpoem .poem-text{display:table !important;margin:0 auto !important;text-align:left}\n"
    "html.kev body #kmain .kpoem .poem-text span{display:block}\n"
    "html.kev body.kendpage #kmain .kframe{-webkit-justify-content:flex-start !important;justify-content:flex-start !important}\n"
    "html.kev body #kmain .kendtxt{text-align:center;padding:14px 7px 16px !important}\n"
    "html.kev body #kmain .kendtxt p,html.kev body #kmain .kendtxt h2{box-shadow:none !important;background:none !important}\n"
    "html.kev body #kmain .kendtxt .kquiet{margin-top:10px !important}\n"
    "html.kev body #kmain .kendtxt .krecap{font:430 17px/23px var(--k-serif) !important;text-align:center !important;border-top:1px solid #000 !important;margin:12px 40px 0 !important;padding:8px 0 0 !important}\n"
    # the bottom panel: drawn for the height it gets, with a frieze or a bead for what is left over
    "html.kev body #kmain .kfill{display:-webkit-flex;display:flex;-webkit-flex-direction:column;flex-direction:column;-webkit-justify-content:space-between !important;"
    "justify-content:space-between !important;height:0;overflow:hidden;margin:0 -6px -5px !important;padding:0 !important;-webkit-flex:none;flex:none}\n"
    "html.kev body #kmain .kfill>div{-webkit-flex:none;flex:none;margin:0 !important}\n"
    "html.kev body #kmain .kfill .kpv{display:none;margin-top:auto !important}\n"
    "html.kev body #kmain#kmain#kmain .kopt{display:none}\n"
    "html.kev body #kmain#kmain .kresume{display:none !important}\n"
    "html.kev body #kmain .ksqz table.kt th,html.kev body #kmain .ksqz table.kt td{padding-top:2px !important;padding-bottom:2px !important}\n"
    "html.kev body #kmain#kmain .ksqz .kp{padding-top:5px !important;padding-bottom:5px !important}\n"
    "html.kev body #kmain#kmain#kmain .ksqz>.kp,html.kev body #kmain#kmain#kmain .ksqz>h2,html.kev body #kmain#kmain#kmain .ksqz>.kbody,html.kev body #kmain#kmain#kmain .ksqz>.kmast{margin-bottom:14px !important}\n"
    "html.kev body #kmain .kfill .kfrule{display:none;height:3px;margin:auto 0 !important;border-top:1.5px solid #000;border-bottom:.5px solid #000}\n"
    "html.kev body #kmain .kp .klow{font:430 17px/23px var(--k-serif) !important}\n"
    "html.kev body #kmain .kp .kbody17{font:430 17px/23px var(--k-serif) !important}\n"
    "html.kev body #kmain .kp .kal2{font:700 17px/23px var(--k-serif) !important;border-bottom:1px solid #000 !important;padding-bottom:4px !important;margin-bottom:4px !important}\n"
    "html.kev body #kmain .kp .kal2 .klb{display:inline;margin-right:10px !important}\n"
    "html.kev body #kmain table.kt.kdaylist.kwide th{width:96px;font:600 13px/23px var(--k-serif) !important;letter-spacing:.12em !important}\n"
    "html.kev body #kmain .kreadline{font:430 15px/20px var(--k-serif) !important;text-align:left !important;margin:-6px 0 8px !important;padding:0 12px !important;"
    "box-shadow:none !important;background:none !important}\n"
    # tomorrow: the figure at the left, the forecast beside it, as on the cover
    "html.kev body #kmain .kalm{display:block !important}\n"
    "html.kev body #kmain .kalm-t{display:grid;grid-template-columns:auto 1fr;-webkit-align-items:center;align-items:center}\n"
    "html.kev body #kmain .kalm-t .kdeg{grid-column:1;grid-row:1}html.kev body #kmain .kalm-t small{grid-column:1;grid-row:2;margin:0 !important}\n"
    "html.kev body #kmain .kalm-t .kalm-lead{grid-column:2;grid-row:1/3;margin:0 0 0 18px !important;padding:0 0 0 18px !important;border-left:1px solid #000 !important;"
    "font:italic 430 24px/31px var(--k-serif) !important}\n"
)


# ---------------------------------------------------------------------------------------------
# Ornaments: line engraving for e-ink. One collector's cabinet: Western scrollwork and acanthus,
# Thai kanok flame-scroll, guilloche, and small Pacific Northwest vignettes, all drawn with the
# same three line weights (W0 hairline, W1 rule, W2 heavy rule) and the same five tones (the
# patterns in ORNAMENTS["defs"]: stipple light/mid, hatch, cross-hatch, dense hatch), never solid
# grey. Every piece is a small inline SVG; the patterns are defined once per page.
# ---------------------------------------------------------------------------------------------
W0, W1, W2 = .6, 1, 1.6
K = 'stroke="#000"'


def _n(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def _css_transform(m):
    """kindle_full's reset sets `transform:none !important` on every element, which would erase SVG
    transform attributes; an inline !important style outranks it. Same geometry, CSS syntax."""
    out = []
    for fn, args in re.findall(r"(\w+)\(([^)]*)\)", m.group(1)):
        a = [x for x in re.split(r"[\s,]+", args.strip()) if x]
        if fn == "translate":
            out.append(f"translate({a[0]}px,{a[1] if len(a) > 1 else 0}px)")
        elif fn == "rotate" and len(a) == 3:
            out.append(f"translate({a[1]}px,{a[2]}px) rotate({a[0]}deg) translate({-float(a[1]):g}px,{-float(a[2]):g}px)")
        elif fn == "rotate":
            out.append(f"rotate({a[0]}deg)")
        elif fn == "scale":
            out.append(f"scale({a[0]},{a[1] if len(a) > 1 else a[0]})")
        elif fn == "matrix":
            out.append(f"matrix({','.join(a)})")
    return f'style="transform:{" ".join(out)} !important"'


def _fix(svg):
    svg = re.sub(r'transform="([^"]+)"', _css_transform, svg)
    # the reset also sets letter-spacing:normal on every element
    return re.sub(r'letter-spacing="([\d.]+)"', r'style="letter-spacing:\1px !important"', svg)


def _svg(w, h, inner, cls="", vb=None, extra=""):
    return _fix(f'<svg class="korn {cls}" width="{_n(w)}" height="{_n(h)}" viewBox="{vb or f"0 0 {_n(w)} {_n(h)}"}" '
                f'aria-hidden="true"{extra}>{inner}</svg>')


def _star(cx, cy, r, w=None):
    """A four-point engraved star."""
    w = r * .2 if w is None else w
    return (f'<path d="M{_n(cx)},{_n(cy - r)}Q{_n(cx + w)},{_n(cy - w)} {_n(cx + r)},{_n(cy)}Q{_n(cx + w)},{_n(cy + w)} '
            f'{_n(cx)},{_n(cy + r)}Q{_n(cx - w)},{_n(cy + w)} {_n(cx - r)},{_n(cy)}Q{_n(cx - w)},{_n(cy - w)} {_n(cx)},{_n(cy - r)}Z"/>')


def _waves(x0, x1, y, amp, period, phase=0.0):
    """A sine-like wave from x0 to x1 (quadratic arcs), as path data."""
    half = period / 2
    x = x0 - phase - period
    d = f"M{_n(x)},{_n(y)}q{_n(half / 2)},{_n(-2 * amp)} {_n(half)},0"
    x += half
    while x < x1:
        d += f"t{_n(half)},0"
        x += half
    return d


def _guilloche_tile(vertical=False):
    """The engine-turned band: four interlaced waves over two shallower ones (12 x 7 tile)."""
    paths = [_waves(0, 12, 3.5, 2.9, 12, ph) for ph in (0, 3, 6, 9)] + [_waves(0, 12, 3.5, 1.2, 6, ph) for ph in (0, 3)]
    g = "".join(f'<path d="{d}"/>' for d in paths)
    if vertical:
        g = re.sub(r"M([-\d.]+),([-\d.]+)q([-\d.]+),([-\d.]+) ([-\d.]+),([-\d.]+)",
                   lambda m: f"M{m[2]},{m[1]}q{m[4]},{m[3]} {m[6]},{m[5]}", g)
        g = re.sub(r"t([-\d.]+),0", r"t0,\1", g)
    return g


def _diag(s, back=False):
    """One tile of 45-degree hatching, seamless (no patternTransform: see _css_transform)."""
    if back:
        return f"M0,0L{_n(s)},{_n(s)}M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(s * 1.5)}M{_n(s / 2)},{_n(-s / 2)}L{_n(s * 1.5)},{_n(s / 2)}"
    return f"M0,{_n(s)}L{_n(s)},0M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(-s / 2)}M{_n(s / 2)},{_n(s * 1.5)}L{_n(s * 1.5)},{_n(s / 2)}"


def _defs():
    pat = ('<pattern id="{id}" width="{w}" height="{h}" patternUnits="userSpaceOnUse"{t}>{c}</pattern>')
    out = [
        pat.format(id="ke-s2", w=4, h=4, t="", c='<circle cx="1" cy="1" r=".42"/><circle cx="3" cy="3" r=".42"/>'),
        pat.format(id="ke-s", w=2.5, h=2.5, t="", c='<circle cx=".625" cy=".625" r=".5"/><circle cx="1.875" cy="1.875" r=".5"/>'),
        pat.format(id="ke-h", w=3.5, h=3.5, t="", c=f'<path d="{_diag(3.5)}" {K} stroke-width=".5"/>'),
        pat.format(id="ke-hv", w=6, h=2.5, t="", c=f'<path d="M0,1.25H4.2" {K} stroke-width=".5"/>'),
        pat.format(id="ke-rule", w=8, h=2, t="", c=f'<path d="M0,1H8" {K} stroke-width=".5"/>'),
        pat.format(id="ke-x", w=3.5, h=3.5, t="", c=f'<path d="{_diag(3.5)}{_diag(3.5, True)}" {K} stroke-width=".5"/>'),
        pat.format(id="ke-rope", w=4, h=6, t="", c=f'<path d="M-1,6.5C.6,4 2.4,1.6 3.4,-.5M3,6.5C4.6,4 6.4,1.6 7.4,-.5" fill="none" {K} stroke-width=".7"/>'),
        pat.format(id="ke-rope-v", w=6, h=4, t="", c=f'<path d="M6.5,-1C4,.6 1.6,2.4 -.5,3.4M6.5,3C4,4.6 1.6,6.4 -.5,7.4" fill="none" {K} stroke-width=".7"/>'),
        pat.format(id="ke-hb", w=6, h=6, t="", c=f'<path d="M0,0L3,3L0,6M3,0L6,3L3,6" fill="none" {K} stroke-width=".5"/>'),
        pat.format(id="ke-hb-v", w=6, h=6, t="", c=f'<path d="M0,0L3,3L6,0M0,3L3,6L6,3" fill="none" {K} stroke-width=".5"/>'),
        pat.format(id="ke-n", w=2, h=2, t="", c=f'<path d="M0,1H2" {K} stroke-width="1"/>'),
        pat.format(id="ke-d", w=2.5, h=2.5, t="", c=f'<path d="{_diag(2.5)}" {K} stroke-width=".5"/>'),
        pat.format(id="ke-p", w=6, h=3, t="", c=f'<path d="M0,1.5Q1.5,0 3,1.5T6,1.5" fill="none" {K} stroke-width=".5"/>'),
        pat.format(id="ke-gh", w=12, h=7, t=' y="3.5"', c=f'<g fill="none" {K} stroke-width=".5">{_guilloche_tile()}</g>'),
        pat.format(id="ke-gv", w=7, h=12, t=' x="3.5"', c=f'<g fill="none" {K} stroke-width=".5">{_guilloche_tile(True)}</g>'),
    ]
    return ('<svg class="kdefs" width="0" height="0" aria-hidden="true" style="position:absolute"><defs>'
            + "".join(out) + "</defs></svg>")


# ---- small motifs, reused everywhere -------------------------------------------------------

def _kanok(x, y, s=1.0, rot=0, flip=False, fill="#fff"):
    """A Thai kanok flame (lai kranok): a leaf whose back sweeps up to a curled tip, with flame licks
    along its belly. Base at (x, y), pointing right before rotation; about 20 x 10 at s=1."""
    sx = -s if flip else s
    return (f'<g transform="translate({_n(x)},{_n(y)}) rotate({_n(rot)}) scale({_n(sx)},{_n(s)})">'
            f'<path d="M0,0C3,-5 9,-9 15,-9.5C18,-9.7 20.5,-8 20,-5.5C19.6,-7 18,-7.6 16.8,-7C18.4,-5.8 17.6,-3.6 15.6,-3.4'
            f'C15.4,-4.4 14.6,-5 13.6,-4.8C14,-3 12.6,-1.4 10.4,-1.4C10.5,-2.4 10,-3.1 9,-3C8.8,-1 6,.2 0,0Z" '
            f'fill="{fill}" {K} stroke-width="{_n(W0 / s)}"/>'
            f'<path d="M1.5,-.8C5,-3.6 10,-6.6 16,-7.6" fill="none" {K} stroke-width="{_n(.45 / s)}"/></g>')


def _leaf(x, y, s=1.0, rot=0, tone="url(#ke-h)"):
    """An acanthus leaf: three lobes, toned on the shadow side, base at (x, y), pointing right."""
    return (f'<g transform="translate({_n(x)},{_n(y)}) rotate({_n(rot)}) scale({_n(s)})">'
            f'<path d="M0,0C3,-5 8,-7 12,-6C10,-5 9.5,-4 10.5,-3.4C12.5,-4.6 15,-4 16.5,-2.6C14.5,-2.4 13.5,-1.6 14,-.6'
            f'C15.5,-1 17.5,0 18.5,1.4C13,2 6,2.2 0,0Z" fill="#fff" {K} stroke-width="{W0}"/>'
            f'<path d="M0,0C5,.6 10,1 18,1.2L14,-.6 10.5,-3.4C7,-1 3,0 0,0Z" fill="{tone}"/>'
            f'<path d="M1,-.4C6,-2 10,-3 13,-3" fill="none" {K} stroke-width="{W0}"/></g>')


def _pearl(cx, cy, r):
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="url(#ke-p)" {K} stroke-width="{W0}"/>'


def _moon_shape(cx, cy, r, lit, waxing, cid, maria=False, dark="url(#ke-x)"):
    """The moon at its phase: the dark side cross-hatched, the lit side white (with stippled seas)."""
    k = max(0.0, min(1.0, lit / 100))
    rx = abs(1 - 2 * k) * r
    sweep = 0 if k < .5 else 1
    lit_d = (f"M{_n(cx)},{_n(cy - r)}A{_n(r)},{_n(r)} 0 0 1 {_n(cx)},{_n(cy + r)}"
             f"A{_n(rx)},{_n(r)} 0 0 {sweep} {_n(cx)},{_n(cy - r)}Z")
    flip = "" if waxing else f' transform="translate({_n(2 * cx)},0) scale(-1,1)"'
    out = f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="{dark}"/>'
    if k > .01:
        if k > .99:
            out += f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="#fff"/>'
            clip_shape = f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}"/>'
        else:
            out += f'<path d="{lit_d}" fill="#fff" {K} stroke-width=".45"{flip}/>'
            clip_shape = f'<path d="{lit_d}"{flip}/>'
        if maria:
            u = r / 50
            seas = [(-16, -20, 12, 11), (8, -18, 8, 7), (14, -4, 9, 8), (30, -12, 5, 6), (-26, 4, 11, 17),
                    (-10, 20, 8, 6), (24, 10, 6, 7), (-2, -4, 5, 4)]
            m = "".join(f'<ellipse cx="{_n(cx + a * u)}" cy="{_n(cy + b * u)}" rx="{_n(c * u)}" ry="{_n(d * u)}"/>'
                        for a, b, c, d in seas)
            craters = "".join(f'<circle cx="{_n(cx + a * u)}" cy="{_n(cy + b * u)}" r="{_n(c * u)}" fill="#fff" {K} stroke-width=".45"/>'
                              for a, b, c in ((-6, 36, 2.6), (20, 28, 1.8), (-34, -14, 1.6), (32, 26, 2.2), (4, 8, 1.4)))
            rays = "".join(f'<path d="M{_n(cx - 6 * u)},{_n(cy + 36 * u)}l{_n(dx * u)},{_n(dy * u)}" {K} stroke-width=".35"/>'
                           for dx, dy in ((-14, -10), (12, -12), (-2, -18), (16, 2), (-16, 4)))
            out += (f'<clipPath id="{cid}">{clip_shape}</clipPath><g clip-path="url(#{cid})">'
                    f'<g fill="url(#ke-s2)">{m}</g>{rays}{craters}</g>')
    out += f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="none" {K} stroke-width="{W1 if r > 12 else W0}"/>'
    return out


def _fir(x, base, h, tone="url(#ke-x)"):
    """A Douglas fir: drooping tiers, toned."""
    w = h * .42
    tiers = 5
    d = f"M{_n(x)},{_n(base - h)}"
    pts_r, pts_l = [], []
    for i in range(1, tiers + 1):
        yy = base - h + h * i / tiers * .92
        ww = w * i / tiers
        pts_r.append(f"L{_n(x + ww)},{_n(yy)}L{_n(x + ww * .45)},{_n(yy - h * .06)}")
        pts_l.append(f"L{_n(x - ww * .45)},{_n(yy - h * .06)}L{_n(x - ww)},{_n(yy)}")
    d += "".join(pts_r[:-1]) + f"L{_n(x + w)},{_n(base - h * .08)}L{_n(x + 1)},{_n(base - h * .08)}L{_n(x + 1)},{_n(base)}" \
         + f"L{_n(x - 1)},{_n(base)}L{_n(x - 1)},{_n(base - h * .08)}L{_n(x - w)},{_n(base - h * .08)}" + "".join(reversed(pts_l[:-1])) + "Z"
    return f'<path d="{d}" fill="{tone}" {K} stroke-width="{W0}" stroke-linejoin="round"/>'


# ---- dividers, tailpieces, flanks ---------------------------------------------------------------

def _divider(w=260):
    """Inlay rule: a pearl lozenge set between acanthus leaves, hairlines ending in small curls."""
    c, y = w / 2, 8
    half = (f'<path d="M{_n(c + 26)},{y}H{_n(w - 12)}" {K} stroke-width="{W0}"/>'
            f'<path d="M{_n(w - 12)},{y}c3.5,0 5,-2.6 3.4,-4.2c-1.4,-1.4 -3.4,0 -2,1.4" fill="none" {K} stroke-width="{W0}"/>'
            + _leaf(c + 10, y, .62, -14) + f'<circle cx="{_n(c + 34)}" cy="{y}" r="1.1"/>')
    mirror = f'<g transform="translate({_n(w)},0) scale(-1,1)">{half}</g>'
    loz = (f'<path d="M{_n(c - 8)},{y}L{_n(c)},{y - 5}L{_n(c + 8)},{y}L{_n(c)},{y + 5}Z" fill="url(#ke-p)" {K} stroke-width="{W1}"/>'
           + _star(c, y, 2.4))
    return _svg(w, 16, half + mirror + loz, "kdiv")


def _tailpiece():
    """Cul-de-lampe: two kanok flames leaving a pearl, acanthus beneath, a falling line of dots."""
    c = 50
    g = (_kanok(c + 5, 11, 1.0) + _kanok(c - 5, 11, 1.0, flip=True)
         + _leaf(c + 3, 14, .55, 30) + f'<g transform="translate({2 * c},0) scale(-1,1)">{_leaf(c + 3, 14, .55, 30)}</g>'
         + _pearl(c, 10, 4) + _star(c, 10, 2)
         + f'<circle cx="{c}" cy="19.5" r="1.3"/><circle cx="{c}" cy="23.5" r=".9"/><circle cx="{c}" cy="26.6" r=".6"/>')
    return _svg(100, 28, g, "ktail")


def _asterism():
    return _svg(30, 18, _star(15, 4.5, 4.2) + _star(8.5, 13, 4.2) + _star(21.5, 13, 4.2), "kast")


def _date_flank():
    """A crescent and two stars on a scrolled stem, for either side of the date line."""
    g = (_moon_shape(9, 8, 5.6, 34, True, "kdf", dark="url(#ke-s)") +
         f'<path d="M17,8C24,8 28,4.5 34,6C38,7 40,10 44,9" fill="none" {K} stroke-width="{W0}"/>'
         + _star(24, 3.4, 2.6) + _star(31, 12, 2) + f'<circle cx="44.5" cy="9" r="1"/>')
    return g


# ---- borders -----------------------------------------------------------------------------------

def _frame_strips():
    """The border family: heavy rule, guilloche band between hairlines, hairline. 14 px deep."""
    h = (f'<path d="M0,.8H9999" {K} stroke-width="{W2}"/><path d="M0,3.2H9999M0,10.8H9999M0,13.2H9999" {K} stroke-width="{W0}"/>'
         f'<rect x="0" y="3.5" width="100%" height="7" fill="url(#ke-gh)"/>')
    v = (f'<path d="M.8,0V9999" {K} stroke-width="{W2}"/><path d="M3.2,0V9999M10.8,0V9999M13.2,0V9999" {K} stroke-width="{W0}"/>'
         f'<rect x="3.5" y="0" width="7" height="100%" fill="url(#ke-gv)"/>')
    return (f'<svg class="kfs kfs-t" aria-hidden="true">{h}</svg><svg class="kfs kfs-b" aria-hidden="true">{h}</svg>'
            f'<svg class="kfs kfs-l" aria-hidden="true">{v}</svg><svg class="kfs kfs-r" aria-hidden="true">{v}</svg>')


def _roundel(subject, cid, corner="tl"):
    """A corner roundel (56 x 56): heavy ring, hairline ring, kanok flames licking along both borders and
    curling inward. Drawn for the top-left corner and mirrored; the subject itself is never mirrored."""
    fx, fy = corner[1] == "r", corner[0] == "b"
    m = f"translate({56 if fx else 0},{56 if fy else 0}) scale({-1 if fx else 1},{-1 if fy else 1})"
    um = f"translate({40 if fx else 0},{40 if fy else 0}) scale({-1 if fx else 1},{-1 if fy else 1})"
    flames = (f'<rect x="38" y="3.6" width="17" height="6.8" fill="#fff"/><rect x="3.6" y="38" width="6.8" height="17" fill="#fff"/>'
              f'<g id="{cid}f"><g transform="translate(38.5,4.2) scale(1,-1)">{_kanok(0, 0, .62, 4)}</g></g>'
              f'<g transform="matrix(0 1 1 0 0 0)"><g transform="translate(38.5,4.2) scale(1,-1)">{_kanok(0, 0, .62, 4)}</g></g>')
    ring = (f'<circle cx="20" cy="20" r="19" fill="#fff" {K} stroke-width="{W2}"/>'
            f'<circle cx="20" cy="20" r="16.2" fill="none" {K} stroke-width="{W0}"/>'
            f'<clipPath id="{cid}"><circle cx="20" cy="20" r="15.6"/></clipPath>'
            f'<g clip-path="url(#{cid})"><g transform="{um}">{subject}</g></g>')
    return _svg(56, 56, f'<g transform="{m}">{flames}{ring}</g>', f"kround kround-{corner}")


def _rosette(cx, cy, R, r, n, sw=.45):
    """Guilloche rosette: n circles of radius r around a ring of radius R."""
    import math as _m
    return "".join(f'<circle cx="{_n(cx + R * _m.cos(2 * _m.pi * i / n))}" cy="{_n(cy + R * _m.sin(2 * _m.pi * i / n))}" '
                   f'r="{_n(r)}" fill="none" {K} stroke-width="{sw}"/>' for i in range(n))


# ---- the corner subjects (40 x 40, centre 20,20) ------------------------------------------------

def _subj_record():
    grooves = "".join(f'<circle cx="20" cy="20" r="{_n(r)}" fill="none" {K} stroke-width=".35"/>' for r in (7.5, 9, 10.5, 12, 13.5))
    return (f'<circle cx="20" cy="20" r="15" fill="url(#ke-d)"/>{grooves}'
            f'<path d="M12,12A11,11 0 0 1 27,10" fill="none" stroke="#fff" stroke-width="1.4"/>'
            f'<circle cx="20" cy="20" r="5" fill="url(#ke-s)" {K} stroke-width="{W0}"/><circle cx="20" cy="20" r=".9" fill="#fff"/>')


def _subj_drums():
    """A snare drum on its stand, tension rods ruled down the shell, two sticks crossed on the head."""
    rods = "".join(f'M{x},{_n(20 + 3.2 * (1 - ((x - 20) / 12) ** 2) ** .5)}V{_n(31 + 3.2 * (1 - ((x - 20) / 12) ** 2) ** .5)}'
                   for x in (10.5, 15, 20, 25, 29.5))
    return (f'<path d="M8,20V31A12,3.4 0 0 0 32,31V20Z" fill="url(#ke-s)" {K} stroke-width="{W0}"/>'
            f'<path d="{rods}" {K} stroke-width=".7"/>'
            f'<path d="M8,31A12,3.4 0 0 0 32,31M8,22.4A12,3.4 0 0 0 32,22.4" fill="none" {K} stroke-width="{W1}"/>'
            f'<ellipse cx="20" cy="20" rx="12" ry="3.4" fill="#fff" {K} stroke-width="{W1}"/>'
            f'<path d="M15,34.4L11,39M25,34.4L29,39M20,34.6V39" {K} stroke-width="{W0}"/>'
            f'<path d="M6,9.5L24,18.6M34,9.5L16,18.6" fill="none" {K} stroke-width="1.5" stroke-linecap="round"/>'
            f'<circle cx="6" cy="9.5" r="1.4"/><circle cx="34" cy="9.5" r="1.4"/>')


def _subj_dog_head():
    """A dog's head in profile, ear down, collar and tag: the corner roundel's dog."""
    return (f'<path d="M11,40C10,32 11,24 14,19C16.5,14.5 20.5,11 25,11C28,11 30.2,12.6 31.2,15L35.6,16.8C37.6,17.8 37.6,20.8 35.6,21.8'
            f'L30.6,23C28.6,25 27,27.6 27,31L28,40Z" fill="#fff" {K} stroke-width="{W1}" stroke-linejoin="round"/>'
            f'<path d="M12.6,40C12,33 12.6,28 14.6,24.6L19,30C20,34 20.6,37 21,40Z" fill="url(#ke-h)"/>'
            f'<path d="M19.4,13.4C14.6,14.4 12.4,19.6 13.2,26.4C15.6,27.6 18,25.6 19,22.4C20,19.2 20.8,15.6 19.4,13.4Z" fill="url(#ke-x)" {K} stroke-width="{W0}"/>'
            f'<circle cx="35.8" cy="18.2" r="1.5"/><circle cx="26.4" cy="15.6" r="1"/>'
            f'<path d="M35.4,21.6C33.6,22.6 31.6,22.6 30.4,22.2M27.4,14.2Q26.4,13.2 25,13.6" fill="none" {K} stroke-width=".5"/>'
            f'<path d="M12,32.4C17,34 23,34 27.4,32" fill="none" {K} stroke-width="1.8"/>'
            f'<circle cx="20" cy="35.6" r="1.6" fill="#fff" {K} stroke-width="{W0}"/>')


def _subj_heron():
    return (f'<path d="M5,33H35" {K} stroke-width="{W0}"/><path d="M8,35.5H16M22,35.5H32" {K} stroke-width=".4"/>'
            f'<path d="M18,22C18,17 21,14 22,11C23,8 21,6.5 19.5,7C18.6,7.3 18.4,8.2 18.8,8.8" fill="none" {K} stroke-width="1.2"/>'
            f'<path d="M19.4,7.2L12.5,8.4L19.6,8.2Z"/>'
            f'<path d="M16,22C18,19 24,18 27,21C29,23 30,26 31,28C27,27 22,27 18,26C16,25 15.5,23.5 16,22Z" fill="url(#ke-h)" {K} stroke-width="{W0}"/>'
            f'<path d="M21,26.5L20,33M23,26.8L24,33" {K} stroke-width="{W0}"/>'
            f'<path d="M10,33C10,28 9,25 7,23M30,33C31,29 33,27 34,26M33,33C33,30 34,29 36,28" fill="none" {K} stroke-width=".45"/>')


def _subj_dog():
    """A dog asleep, curled nose to tail."""
    return (f'<ellipse cx="20" cy="31" rx="15" ry="3" fill="url(#ke-s2)" {K} stroke-width=".4"/>'
            f'<path d="M7,29C6,22 12,17 20,17C28,17 33,22 32,28C31,30 28,30.5 25,30.5H10C8,30.5 7,30 7,29Z" fill="url(#ke-h)" {K} stroke-width="{W0}"/>'
            f'<path d="M24,29C23,25 26,22.5 29.5,23.5C32,24.3 32.5,27 31,28.6C29,30 26,30.3 24,29Z" fill="#fff" {K} stroke-width="{W0}"/>'
            f'<path d="M27,23.6C25.5,21 26,19.5 28,19C28.6,21 28.6,22.5 28,23.8Z" fill="url(#ke-x)" {K} stroke-width="{W0}"/>'
            f'<path d="M28.6,26.4Q29.6,27 30.6,26.4" fill="none" {K} stroke-width=".5"/><circle cx="31.4" cy="27.6" r=".7"/>'
            f'<path d="M9,29C11,26 15,26 19,28.5" fill="none" {K} stroke-width="{W0}"/>'
            f'<path d="M9.5,24C11,21 14,19.6 17,19.4M11,27C13,24 16,22.6 20,22.5" fill="none" stroke="#fff" stroke-width=".8"/>')


def _subj_rosette():
    return _rosette(20, 20, 6.5, 8.5, 18) + f'<circle cx="20" cy="20" r="2.4" fill="#fff" {K} stroke-width="{W0}"/>' + _star(20, 20, 1.8)


# ---- the vignettes ---------------------------------------------------------------------------

def _hood(cx, base, s=1.0):
    """Mount Hood: snow above a ragged line, the east face hatched, the lower slopes stippled."""
    def p(x, y):
        return f"{_n(cx + x * s)},{_n(base + y * s)}"
    hill = f"M{p(-58, 0)}L{p(-28, -20)}L{p(-14, -29)}L{p(-5, -36)}L{p(0, -40)}L{p(5, -35)}L{p(14, -28)}L{p(28, -18)}L{p(60, 0)}Z"
    shade = f"M{p(0, -40)}L{p(5, -35)}L{p(14, -28)}L{p(28, -18)}L{p(60, 0)}L{p(8, 0)}L{p(3, -22)}Z"
    snow = (f"M{p(-20, -24)}l{_n(3 * s)},{_n(3 * s)} {_n(3 * s)},{_n(-2 * s)} {_n(4 * s)},{_n(5 * s)} {_n(3 * s)},{_n(-4 * s)} "
            f"{_n(4 * s)},{_n(4 * s)} {_n(3 * s)},{_n(-5 * s)} {_n(4 * s)},{_n(4 * s)} {_n(3 * s)},{_n(-3 * s)} {_n(4 * s)},{_n(3 * s)} {_n(4 * s)},{_n(-2 * s)}")
    low = snow + f"L{p(28, -18)}L{p(60, 0)}L{p(-58, 0)}L{p(-28, -20)}Z"
    return (f'<path d="{hill}" fill="#fff" {K} stroke-width="{W0}" stroke-linejoin="round"/>'
            f'<path d="{low}" fill="url(#ke-s)"/><path d="{shade}" fill="url(#ke-h)"/>'
            f'<path d="{snow}" fill="none" {K} stroke-width=".45"/>'
            f'<path d="M{p(0, -40)}L{p(-3, -28)}M{p(0, -40)}L{p(2, -27)}M{p(-5, -36)}L{p(-10, -26)}" fill="none" {K} stroke-width=".4"/>')


def _water(x0, x1, y0, y1, gap_at=None):
    """River: broken horizontal hairlines, a white path where the moon lies on the water."""
    lines, y, i = [], y0 + 1.5, 0
    while y < y1:
        x = x0 + (i * 7) % 11
        while x < x1:
            ln = 6 + (i * 5 + int(x)) % 9
            if not (gap_at and abs(x + ln / 2 - gap_at) < 4 + (y - y0) * .5):
                lines.append(f"M{_n(x)},{_n(y)}h{_n(ln)}")
            x += ln + 3 + (i * 3 + int(x)) % 4
        y += 2.4 if y < (y0 + y1) / 2 else 2.0
        i += 1
    return f'<path d="{"".join(lines)}" {K} stroke-width=".45"/>'


def _vig_hood():
    """The cover's central vignette: Mount Hood under the moon, firs, the Columbia in front. 200 x 84."""
    sky = (f'<rect width="200" height="84" fill="url(#ke-s2)"/><rect width="200" height="26" fill="url(#ke-s2)" transform="translate(2,2)"/>'
           f'<circle cx="150" cy="22" r="15" fill="#fff"/><circle cx="150" cy="22" r="13" fill="none" {K} stroke-width=".35" stroke-dasharray="1 2"/>')
    stars = "".join(_star(x, y, r) for x, y, r in ((40, 14, 2.6), (62, 26, 1.6), (112, 12, 1.8), (178, 40, 1.6), (24, 32, 1.4), (90, 8, 1.3)))
    moon = _moon_shape(150, 22, 8.5, 24, True, "kvm", dark="url(#ke-h)")
    hills = (f'<path d="M0,58C20,52 34,55 48,52C60,50 70,56 82,55C100,54 112,50 126,53C142,56 160,50 176,52C186,53 194,51 200,52V72H0Z" '
             f'fill="url(#ke-x)" {K} stroke-width="{W0}"/>')
    firs = "".join(_fir(x, b, h) for x, b, h in ((14, 64, 20), (24, 66, 15), (34, 64, 22), (170, 64, 20), (182, 66, 24), (192, 64, 17), (160, 66, 13)))
    river = (f'<rect y="66" width="200" height="18" fill="#fff"/><path d="M0,66H200" {K} stroke-width="{W0}"/>' + _water(0, 200, 66, 84, 150))
    g = sky + stars + moon + _hood(100, 60, 1.05) + hills + firs + river
    return (f'<clipPath id="kvc"><ellipse cx="100" cy="42" rx="99" ry="41"/></clipPath><g clip-path="url(#kvc)">{g}</g>'
            f'<ellipse cx="100" cy="42" rx="99" ry="41" fill="none" {K} stroke-width="{W1}"/>')


def _scroll_flank():
    """Acanthus scrollwork leaving the vignette's frame to the left: a volute, leaves and a kanok tip. 150 x 84."""
    stems = (f'<path d="M150,40C126,40 112,22 86,22C60,22 44,36 50,52C55,64 72,62 72,52C72,45 63,44 61,50C60,53 63,55 65,53" '
             f'fill="none" {K} stroke-width="{W1}"/>'
             f'<path d="M150,46C130,48 118,66 96,66C82,66 76,74 82,79C86,82 90,78 88,76" fill="none" {K} stroke-width="{W0}"/>'
             f'<path d="M86,22C74,18 62,10 46,14C34,17 28,26 34,31C38,34 42,30 40,28" fill="none" {K} stroke-width="{W0}"/>')
    leaves = (_leaf(128, 35, 1.1, 200) + _leaf(108, 25, 1.0, 196) + _leaf(118, 54, .9, 160) + _leaf(98, 64, .8, 170)
              + _leaf(60, 18, .8, 210) + _leaf(52, 40, .75, 250))
    tips = _kanok(36, 52, 1.0, 190, False) + _kanok(30, 74, .85, 170, True)
    pearls = _pearl(20, 44, 3) + f'<circle cx="12" cy="44" r="1.2"/><circle cx="6" cy="44" r=".8"/>' + _pearl(65, 53, 1.6)
    return stems + leaves + tips + pearls


def _cover_centrepiece(w):
    """Scrollwork flanking the oval vignette, scaled to the measure."""
    side = (w - 200) / 2
    s = side / 150
    left = f'<g transform="translate(0,0) scale({_n(s)},1)">{_scroll_flank()}</g>'
    right = f'<g transform="translate({_n(w)},0) scale({_n(-s)},1)">{_scroll_flank()}</g>'
    def med(cx, subject, cid):
        return (f'<circle cx="{cx}" cy="42" r="19" fill="#fff" {K} stroke-width="{W2}"/>'
                f'<circle cx="{cx}" cy="42" r="16.4" fill="none" {K} stroke-width="{W0}" stroke-dasharray="1 1.6"/>'
                f'<clipPath id="{cid}"><circle cx="{cx}" cy="42" r="15.4"/></clipPath><g clip-path="url(#{cid})">{subject}</g>')
    bridge = ORNAMENTS_BRIDGE_INNER()
    cranes = _crane(23, 38, .62) + _crane(14, 50, .45) + "".join(_star(x, y, 1.4) for x, y in ((10, 32), (30, 54)))
    meds = (med(21, cranes, "kmc") + med(_n(w - 21), f'<g transform="translate({_n(w - 21 - 66 * .5)},26) scale(.5)">{bridge}</g>', "kmb"))
    return _svg(w, 84, left + right + f'<g transform="translate({_n(side)},0)">{_vig_hood()}</g>' + meds, "kcentre")


def _tonight_oval(night, mo, phase, pl, w=236, h=96):
    """Tonight's real sky over Mount Hood in an engraved oval: the moon at its true phase and place,
    the bright planets lettered, a star field seeded by the date. Drawn about (0, 0)-(w, h)."""
    cx, ry, rx, hz = w / 2, h / 2 - 1, w / 2 - 1, 66
    rnd = engraving.rng_for(night, "stars")

    def at(dirn, alt):
        az = AZ.get(dirn, 180)
        x = cx + max(-1, min(1, (az - 180) / 110)) * (rx - 30)
        y = hz - 10 - max(0, min(80, alt)) / 80 * (hz - 22)
        return x, y
    marks, avoid, boxes = [], [], []
    hx = cx + (113 - 180) / 110 * (rx - 30)  # Mt Hood at its true bearing from the island
    if mo and phase:
        x, y = at(mo["dir"], mo["alt"])
        avoid.append((x, y, 11))
        marks.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="10" fill="#fff"/>' + _moon_shape(x, y, 7.5, phase[0], phase[1], "kom", dark="url(#ke-n)"))
    for p in pl:
        x, y = at(p["dir"], p["alt"])
        while any(abs(x - a) < 14 and abs(y - b) < 16 for a, b, _ in avoid):
            x += 18 if x < cx + 60 else -18
            y += 5
        avoid.append((x, y, 9))
        lab = p["name"]
        lw = 4.3 * len(lab) + 6
        lx = x + 8 if x < cx + 40 else x - 8 - lw
        ly = y
        lx = max(cx - rx + 16, min(cx + rx - 16 - lw, lx))

        def hit(a, b):
            return any(a < bx + bw + 2 and bx < a + lw + 2 and abs(b - by) < 11 for bx, by, bw in boxes)
        if hit(lx, ly):
            lx = max(cx - rx + 16, min(cx + rx - 16 - lw, x - 8 - lw if lx > x else x + 8))
        if hit(lx, ly):
            ly = y + 11
        boxes.append((lx, ly, lw))
        avoid.append((lx + lw / 2, y + 9, lw / 2 + 2))
        marks.insert(0, f'<circle cx="{_n(x)}" cy="{_n(y)}" r="6" fill="#fff"/>' + _star(x, y, 5, .9)
                     + f'<circle cx="{_n(x)}" cy="{_n(y)}" r="1.4" fill="#fff" {K} stroke-width=".5"/>')
        marks.append(f'<rect x="{_n(lx)}" y="{_n(ly + 3.4)}" width="{_n(lw)}" height="10" fill="#fff"/>'
                     + f'<text x="{_n(lx + 3)}" y="{_n(ly + 11)}" class="ksm">{E(lab)}</text>')
    field = engraving.stars(rnd, 34, (6, 6, w - 6, hz - 14), avoid + [(hx, hz - 20, 26)])
    st = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r + 1)}" fill="#fff"/><circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}"/>'
                 for x, y, r in field[:28])
    st += "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="3.2" fill="#fff"/>' + _star(x, y, 2.6) for x, y, _ in field[28:])
    sky = f'<rect width="{w}" height="{h}" fill="url(#ke-rule)"/>'
    hills = (f'<path d="M0,{hz - 6}C24,{hz - 12} 40,{hz - 9} 58,{hz - 12}C76,{hz - 14} 90,{hz - 8} 104,{hz - 9}C130,{hz - 10} 150,{hz - 14} 176,{hz - 10}'
             f'C196,{hz - 7} 214,{hz - 11} {w},{hz - 9}V{hz + 4}H0Z" fill="url(#ke-x)" {K} stroke-width="{W0}"/>')
    firs = "".join(_fir(x, b, hh) for x, b, hh in ((12, hz + 1, 20), (22, hz + 2, 14), (150, hz + 2, 13), (196, hz, 22), (208, hz + 2, 26), (220, hz, 18), (184, hz + 2, 14)))
    river = f'<rect y="{hz}" width="{w}" height="{h - hz}" fill="#fff"/><path d="M0,{hz}H{w}" {K} stroke-width="{W0}"/>' + _water(0, w, hz, h, None)
    g = sky + st + _hood(hx, hz - 4, .78) + hills + firs + river + "".join(marks)
    return (f'<clipPath id="koc"><ellipse cx="{_n(cx)}" cy="{_n(h / 2)}" rx="{_n(rx)}" ry="{_n(ry)}"/></clipPath><g clip-path="url(#koc)">{g}</g>'
            f'<ellipse cx="{_n(cx)}" cy="{_n(h / 2)}" rx="{_n(rx)}" ry="{_n(ry)}" fill="none" {K} stroke-width="{W2}"/>'
            f'<ellipse cx="{_n(cx)}" cy="{_n(h / 2)}" rx="{_n(rx - 2.6)}" ry="{_n(ry - 2.6)}" fill="none" {K} stroke-width="{W0}"/>')


def _night_plate(w, night, mo, phase, pl, micro=""):
    """The cover's plate, engraved fresh each night: the edition seal (a rose-engine rosette, tonight's
    number at its boss), tonight's sky in the oval, the moon at its phase in a guilloche ring, and a
    guilloche ribbon tying them together. Every curve is seeded by the date."""
    h, R = 104, 46
    cy = h / 2
    yday = night.timetuple().tm_yday
    ring_txt = ""
    if micro:  # banknote microtext round the seal: discoverable on a second look
        ring_txt = (f'<path id="kpsr" d="M0,-44.4A44.4,44.4 0 1 1 -.1,-44.4" fill="none"/>'
                    f'<text class="kmicro" textLength="276" lengthAdjust="spacing"><textPath href="#kpsr" xlink:href="#kpsr">{micro} &#183; </textPath></text>')
    seal = (f'<g transform="translate({R + 5},{_n(cy)})">'
            f'<circle r="{R + 5}" fill="#fff" {K} stroke-width="{W1}"/><circle r="{R + 3.6}" fill="none" {K} stroke-width="{W0}"/>' + ring_txt
            + engraving.rosette(engraving.rng_for(night, "seal"), "kps", 42.5)
            + f'<text x="0" y="-5" text-anchor="middle" class="ksealno">No.</text>'
            f'<text x="0" y="10" text-anchor="middle" class="kseal">{yday}</text></g>')
    lit, waxing = (phase[0], phase[1]) if phase else (50, True)
    mx = w - R - 5
    moon = (f'<g transform="translate({_n(mx)},{_n(cy)})">'
            f'<circle r="{R + 5}" fill="#fff" {K} stroke-width="{W1}"/><circle r="{R + 3.6}" fill="none" {K} stroke-width="{W0}"/>'
            f'<circle r="{R - 2.6}" fill="#fff" {K} stroke-width="{W2}"/>'
            + engraving.ring(engraving.rng_for(night, "moon"), "kpm", 29.6, R - 4.4)
            + f'<circle r="29.4" fill="#fff" {K} stroke-width="{W0}"/></g>'
            + _moon_shape(mx, cy, 26, lit, waxing, "kpmc", maria=True, dark="url(#ke-rule)"))
    try:  # the bulino portrait moon (e-ink safe hatch, phase-correct); sized so its bezel sits inside the boss
        import math as _m
        from .engraving_eink import engraved_portrait_moon
        _ph = _m.acos(max(-1.0, min(1.0, 1 - 2 * lit / 100.0))) / (2 * _m.pi)
        _pm = engraved_portrait_moon(_ph if waxing else 1 - _ph, 19, cx=mx, cy=cy, seed=7,
                                     standalone=False, label=False)
        moon = moon.rsplit(_moon_shape(mx, cy, 26, lit, waxing, "kpmc", maria=True, dark="url(#ke-rule)"), 1)[0] + _pm
    except Exception:
        pass
    ow = 236
    ox = (w - ow) / 2
    rib_y = cy - 8
    rib = ""
    for x0, x1 in ((2 * R + 10, ox + 8), (ox + ow - 8, w - 2 * R - 10)):
        rib += (f'<rect x="{_n(x0)}" y="{_n(rib_y)}" width="{_n(x1 - x0)}" height="16" fill="#fff"/>'
                f'<clipPath id="kpr{int(x0)}"><rect x="{_n(x0)}" y="{_n(rib_y + 1.4)}" width="{_n(x1 - x0)}" height="13.2"/></clipPath>'
                f'<g clip-path="url(#kpr{int(x0)})"><g transform="translate({_n(x0)},{_n(rib_y + 1.4)})">'
                + engraving.band(engraving.rng_for(night, f"rib{int(x0)}"), f"kpb{int(x0)}", x1 - x0, 13.2) + '</g></g>'
                f'<path d="M{_n(x0)},{_n(rib_y)}H{_n(x1)}M{_n(x0)},{_n(rib_y + 16)}H{_n(x1)}" {K} stroke-width="{W1}"/>')
    flourish = (_kanok(2 * R + 12, rib_y - 6, .55, 0) + _kanok(w - 2 * R - 12, rib_y - 6, .55, flip=True)
                + _leaf(2 * R + 12, rib_y + 23, .5, 6) + f'<g transform="translate({_n(w)},0) scale(-1,1)">{_leaf(2 * R + 12, rib_y + 23, .5, 6)}</g>')
    oval = f'<g transform="translate({_n(ox)},4)">{_tonight_oval(night, mo, phase, pl, ow, 96)}</g>'
    paw = _egg("paw", night.toordinal(), 8)
    paw = f'<g transform="translate({2 * R + 22},{_n(rib_y + 22)})">{paw}</g>' if paw else ""
    return _svg(w, h, rib + flourish + paw + oval + seal + moon, "kcentre kplate2")


def _vig(key, fallback):
    """A vignette from the engravers' set, sized for the story head, or the house ornament without it."""
    v = VIGNETTES.get(key)
    if not v:
        return fallback
    return _fix(v.replace("<svg ", '<svg class="korn kvig kvig2" aria-hidden="true" ', 1))


def _egg(kind, seed, size):
    """One of the engravers' hidden marks (a paw, the butler's A), or nothing without the module."""
    try:
        return engraving_medallions.easter_egg(kind, seed, size) if engraving_medallions else ""
    except Exception:  # noqa: BLE001
        return ""


_THEME_FOR = {"cover": "river", "day1": "jazz", "day2": "river", "day3": "lotus", "local": "bridge", "tomorrow": "river",
              "sky": "sky", "poem": "night", "goodnight": "arms", "index": "river"}


_ART = {"dir": None, "done": {}}


def _art(name, make):
    """Draw a piece once per build and return its URL (relative to the pages)."""
    if name not in _ART["done"]:
        _ART["done"][name] = _at.write(_ART["dir"], name, make())
    return _ART["done"][name]


def _filler(night, salt, w=None, moon=None, budget=90000):
    """The bottom panel for the room a page's words leave: one composed plate (scrollwork springing from
    its frame and wrapping the page's scene) drawn for each height it may take, plus two friezes and a
    bead for what is left over. FILL_JS measures the room and shows the pieces that fit; nothing is
    cropped, and only the panel that is shown is fetched."""
    theme = _THEME_FOR.get(salt, "river")
    if moon is None:
        try:
            moon = _cycle(moon_phase(night))
        except Exception:  # noqa: BLE001
            moon = .5
    out = []
    hs = {"arms": (160, 200, 240, 280, 320, 360, 400)}.get(theme, _at.HEIGHTS if salt in ("tomorrow", "sky", "poem") else _at.HEIGHTS[:6])
    for H in hs:
        try:
            if theme == "arms":   # the last page: the arms above, the sleeping dog on the river and the bridge beneath
                url = _art(f"arms-{H}.svg", lambda: _at.arms_panel(_at.PANEL_W, H, _at._seed("arms"), flank=("dog", "bridge"), moon=moon))
            else:
                url = _art(f"{theme}-{H}.svg", lambda: _at.panel(_at.PANEL_W, H, theme, _at._seed(theme, H), moon))
        except Exception:  # noqa: BLE001
            continue
        out.append(f'<div class="kpv" data-h="{H}" style="height:{H}px;background:url({url}) 50% 100%/{_at.PANEL_W}px {H}px no-repeat !important"></div>')
    return '<div class="kfill" aria-hidden="true"><div class="kfrule"></div>' + "".join(out) + '</div>'


def _cycle(phase):
    """(lit %, waxing) -> the scenes' moon phase: 0 new, .5 full, 1 new again."""
    try:
        lit, waxing = phase[0], phase[1]
        f = max(.11, min(1.0, lit / 100.0))        # under about 10% lit the scenes show a thin crescent, never a dark disc
        p = math.acos(1 - 2 * f) / (2 * math.pi)
        return p if waxing else 1 - p
    except Exception:  # noqa: BLE001
        return .5


def _top(label, salt, night):
    """The page's title plaque, set into the top band of the frame."""
    lw = _at.label_width(label)
    try:
        url = _art(f"top-{lw}.svg", lambda: _at.top_band(lw, 5))
    except Exception:  # noqa: BLE001
        return f'<div class="ktop"><span>{label}</span></div>'
    return f'<div class="ktop" style="background:url({url}) 0 0/{_at.TOP_W}px {_at.BAND}px no-repeat !important"><span>{label}</span></div>'


# ---- one composed plate per page ------------------------------------------------------------------
# Each page's free room takes ONE engraved plate, banknote-vignette style: open, vignetted edges, no box.
# The plate is drawn at a few heights; FILL_JS picks the smallest one that covers the room and crops it
# from the top (the sky), so the line work is never rescaled.
_PLATE_FOR = {"index": "river", "cover": "river", "tomorrow": "river", "sky": "bridge", "local": "bridge",
              "poem": "bridge", "goodnight": "river"}


def _plate_mod(name):
    try:
        import importlib
        return importlib.import_module(f".{name}", __package__)
    except Exception:  # noqa: BLE001
        return None


def _pano_tall(w, H, seed, moon):
    """Fallback plate: the Columbia panorama at the foot, its night sky carried up and opening out
    into the paper, lines breaking off toward the edges; stars knocked out of the sky."""
    import random as _r
    ph = int(min(140, max(60, H)))
    pv = engraving_panorama.panorama(w, ph, seed, moon if moon is not None else .5)
    pv = re.sub(r'</g><rect x="1" y="1".*?</svg>$', '</g></svg>', pv, flags=re.S)
    pv = re.sub(r'<rect width="[\d.]+" height="[\d.]+" fill="#fff"/>', '', pv, 1)
    inner = re.sub(r'^<svg[^>]*>', '', pv)[:-6]
    rng = _r.Random(f"{seed}t")
    top = H - ph
    d = []
    if top > 4:
        y = top + 4 - 1.3
        k = 0
        while y > 2:
            u = (top + 4 - y) / max(1.0, top)  # 0 at the seam, 1 at the top
            half = (w / 2 - 6) * (1 - .55 * u ** 1.4) + rng.uniform(-6, 6)
            x = w / 2 - half
            while x < w / 2 + half:
                ln = rng.uniform(30, 120) * (1 - .6 * u)
                e = min(x + ln, w / 2 + half)
                d.append(f"M{x:.1f} {y:.1f}H{e:.1f}")
                x = e + rng.uniform(2, 4) + rng.uniform(0, 26) * u * u
            y -= 1.3 + 4.2 * u ** 1.3
            k += 1
    stars = []
    for _ in range(int(w * max(0, top) / 2600)):
        sx, sy = rng.uniform(40, w - 40), rng.uniform(6, max(8, top - 4))
        r = rng.choice((1.2, 1.6, 2.2))
        stars.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r + 1.1:.1f}" fill="#fff"/>'
                     f'<path d="M{sx - r:.1f} {sy:.1f}H{sx + r:.1f}M{sx:.1f} {sy - r:.1f}V{sy + r:.1f}" stroke="#000" stroke-width=".5"/>')
    mid = f"kpm{seed}".replace(" ", "")
    mask = (f'<defs><linearGradient id="{mid}g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#000"/>'
            f'<stop offset=".07" stop-color="#fff"/><stop offset=".93" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
            f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{H}"><rect width="{w}" height="{H}" fill="url(#{mid}g)"/></mask></defs>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {H}" width="{w}" height="{H}">{mask}'
            f'<g mask="url(#{mid})"><path d="{"".join(d)}" stroke="#000" stroke-width=".4" fill="none"/>{"".join(stars)}'
            f'<g transform="translate(0,{top})">{inner}</g></g></svg>')


def _one_plate(kind, w, h, seed, moon):
    mp = moon if moon is not None else .5
    try:
        if kind == "jazz":
            m = _plate_mod("plate_jazz")
            if m:
                return m.plate(w, h, seed)
        elif kind == "lotus":
            m = _plate_mod("plate_thai")
            if m:
                return m.lotus(w, h, seed)
        elif kind == "bridge":
            m = _plate_mod("plate_thai")
            if m:
                return m.bridge(w, h, seed, mp)
        m = _plate_mod("plate_river")
        if m:
            return m.plate(w, h, seed, mp)
    except Exception:  # noqa: BLE001
        pass
    if engraving_panorama:
        return _pano_tall(w, h, seed, mp)
    return ""


def _plate_stack(night, salt, seed, w, moon, budget):
    kind = _PLATE_FOR.get(salt, "jazz")
    if moon is None:
        try:
            moon = moon_phase(night)[0] / 100
        except Exception:  # noqa: BLE001
            moon = .5
    out, spent = [], 0
    for H in ((80, 420, 300, 210, 150, 110) if budget > 130000 else (80, 150, 300, 420, 110, 210)):  # a short page leaves a tall room: the big plates first
        try:
            import zlib
            # the jazz frieze only works short; a tall room takes the river
            sv = _one_plate(kind if (kind != "jazz" or H < 170) else "river", w, H, zlib.crc32(f"{salt}{seed}".encode()) % 100000, moon)
        except Exception:  # noqa: BLE001
            sv = ""
        if not sv:
            continue
        sv = re.sub(r'\bid="', f'id="p{H}', sv)
        sv = re.sub(r'url\(#', f'url(#p{H}', sv)
        sv = re.sub(r'href="#', f'href="#p{H}', sv)
        # kindle_full resets transform on every element: carry the plate's transforms as !important styles
        sv = _fix(re.sub(r'patternTransform="([^"]+)"', lambda q: _css_transform(q).replace("transform:", "transform:", 1), sv))
        if spent + len(sv) > budget and out:
            continue
        spent += len(sv)
        sv = re.sub(r'<svg ', f'<svg class="kpv" data-h="{H}" aria-hidden="true" preserveAspectRatio="xMidYMax slice" ', sv, 1)
        out.append(sv)
    out.sort(key=lambda x: int(re.search(r'data-h="(\d+)"', x).group(1)))
    return f'<div class="kplate1">{"".join(out)}</div>' if out else ""


_HEAD_FOR = {"day-1": "jazz", "day-2": "river", "day-3": "lotus", "local": "bridge", "poem": "river"}


def _head_plate(fname, night, h=56):
    """A story's headpiece: a long, open-edged engraved frieze (jazz, the river, the lotus pond, the
    St Johns Bridge) in place of the small boxed vignette, the same height so the page still fits."""
    salt = fname.split(".")[0]
    kind = _HEAD_FOR.get(salt)
    if not kind:
        return ""
    try:
        import zlib
        try:
            moon = moon_phase(night)[0] / 100
        except Exception:  # noqa: BLE001
            moon = .5
        sv = _one_plate(kind, 528, h, zlib.crc32(f"h{salt}{night}".encode()) % 100000, moon)
        if not sv:
            return ""
        sv = re.sub(r'\bid="', 'id="h', sv)
        sv = re.sub(r'url\(#', 'url(#h', sv)
        sv = re.sub(r'href="#', 'href="#h', sv)
        sv = _fix(re.sub(r'patternTransform="([^"]+)"', _css_transform, sv))
        return re.sub(r'<svg ', f'<svg class="korn khp" aria-hidden="true" preserveAspectRatio="xMidYMid meet" ', sv, 1)
    except Exception:  # noqa: BLE001
        return ""


_MED_ORDER = ("snare", "paw", "vinyl", "fir", "rose", "salmon", "bass", "sticks", "moon", "sun")
_VIG_ORDER = ("jazz", "dog", "hood", "drums", "record", "firs", "heron", "river", "cranes", "lotus", "solar", "bridge")


def _fill_stack(night, salt, seed, w, moon, budget=90000):
    """Stacked engraved art for big free areas: medallion rows, vignette rows, the river panorama, a rosette
    panel and Thai ribbons, each a .kfi with its height in data-h; FILL_JS shows them greedily to the exact room.
    Each engraving is drawn once in a hidden defs block and placed by <use>, so a page can stack many rows cheaply."""
    defs, items = [], []
    k = seed % 97
    spent = [0]
    if budget < 12000:  # no room in the page's weight for more than a ribbon
        budget = 0
    XL = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

    def use(ref, vw, vh, dw, dh, extra=""):
        return (f'<svg {XL} viewBox="0 0 {vw} {vh}" width="{_n(dw)}" height="{_n(dh)}" aria-hidden="true"{extra}>'
                f'<use xlink:href="#{ref}" width="{vw}" height="{vh}"/></svg>')

    meds = []
    try:
        if engraving_medallions:
            for i in range(8):
                key = _MED_ORDER[(k + i) % len(_MED_ORDER)]
                m = engraving_medallions.MEDALLIONS[key](40, seed=(k * 7 + i) % 50 + 1)
                if i >= 3 and spent[0] + len(m) > budget * .45:
                    break
                mid = f"kmd{salt}{i}"
                # the medallion's field takes a fine stipple, so it reads as engraved, not as a white hole
                m = re.sub(r'(<path d="[^"]*") fill="#fff"/>', lambda q: q.group(1) + ' fill="#fff"/>' + q.group(1) + f' fill="url(#kst{salt})"/>', m, 1)
                defs.append(m.replace("<svg ", f'<svg id="{mid}" ', 1))
                spent[0] += len(m)
                meds.append(mid)
    except Exception:  # noqa: BLE001
        meds = []
    vigs = []
    try:
        if VIGNETTES:
            for i in range(6):
                key = _VIG_ORDER[(k + i) % len(_VIG_ORDER)]
                v = VIGNETTES.get(key)
                if v and i >= 2 and spent[0] + len(v) > budget * .8:
                    break
                if v:
                    spent[0] += len(v)
                    vid = f"kvg{salt}{i}"
                    defs.append(v.replace("<svg ", f'<svg id="{vid}" ', 1))
                    vigs.append(vid)
    except Exception:  # noqa: BLE001
        vigs = []

    def medrow(n, off):
        d = int((w - 8 * n - 6) / n)  # whole medallions, 4 px either side, centred: never cut at the frame
        h = d + 6
        return h, f'<div class="kfi kfrow" data-h="{h}">' + "".join(use(meds[(off + i) % len(meds)], 100, 100, d, d) for i in range(n)) + '</div>'

    def vigrow(n, off):
        vw = int((w - 8 * n - 6) / n)  # the size stays fixed (one scale on the page)
        vh = vw * 2 / 3
        h = int(vh) + 6
        k = min(n, len(vigs))  # never the same scene twice in a row; medallions take any spare places
        pieces = [use(vigs[(off + i) % len(vigs)], 120, 80, vw, vh) for i in range(k)]
        if k < n and meds:
            m = int((w - 6 - k * (vw + 8)) / (vh + 8))
            md = [use(meds[(off + j) % len(meds)], 100, 100, vh, vh) for j in range(m)]
            pieces = md[:m // 2] + pieces + md[m // 2:]
        return h, f'<div class="kfi kfrow" data-h="{h}">' + "".join(pieces) + '</div>'

    pano = rose = ""
    try:
        if engraving_panorama and budget - spent[0] > 26000:
            pv = engraving_panorama.panorama(w, 104, f"{seed}s", moon if moon is not None else .5)
            pano = f'<div class="kfi" data-h="108">{pv.replace("<svg ", "<svg aria-hidden=" + chr(34) + "true" + chr(34) + " ", 1)}</div>'
    except Exception:  # noqa: BLE001
        pass
    try:
        c = w / 2
        rid = f"kq{salt}"
        g = (f'<g id="{rid}"><circle r="39" fill="#fff" {K} stroke-width="{W1}"/>'
             + engraving.rosette(engraving.rng_for(night, f"{salt}q"), f"kq{salt}p", 36) + '</g>')
        g = f'<g transform="translate({_n(c)},40)">{g}</g>' + "".join(
            f'<use {XL} xlink:href="#{rid}" transform="translate({_n(x)},40)"/>' for x in (c - 180, c + 180))
        g += "".join(_star(x, 40, 6) for x in (c - 180, c, c + 180))
        g += "".join(_kanok(x, 40, .8, r) for x, r in ((c - 95, 180), (c - 85, 0), (c + 85, 180), (c + 95, 0)))
        rose = f'<div class="kfi" data-h="84">' + _fix(f'<svg {XL} viewBox="0 0 {w} 80" width="{w}" height="80" aria-hidden="true">{g}</svg>') + '</div>'
    except Exception:  # noqa: BLE001
        pass
    rib = ""
    try:
        if engraving_thai:
            kb = engraving_thai.kranok_band(w, 16, seed * 3 + 11)
            rib = re.sub(r'<svg ', '<svg aria-hidden="true" preserveAspectRatio="none" style="width:100%;height:16px" ', kb, 1)
    except Exception:  # noqa: BLE001
        pass

    # the menu, best first; the script takes what fits, top to bottom
    if not budget:
        meds = vigs = []
        defs = []
        pano = rose = ""
    # one scale throughout: medallion rows ten across (~45 px, the head row's size), vignette rows six across
    if meds:
        items.append(medrow(10, 0))
    if vigs:
        items.append(vigrow(6, 0))
    if pano:
        items.append((108, pano))
    if meds:
        items.append(medrow(10, 5))
    if rose:
        items.append((84, rose))
    if vigs:
        items.append(vigrow(6, 3))
    if meds:
        items.append(medrow(10, 3))
        items.append(medrow(10, 7))
    if vigs:
        items.append(vigrow(6, 1))
    if meds:
        items.append(medrow(10, 1))
    if rib:
        items.append((20, f'<div class="kfi" data-h="20">{rib}</div>'))
    if defs:
        defs.insert(0, f'<svg width="0" height="0"><defs><pattern id="kst{salt}" width="3" height="3" patternUnits="userSpaceOnUse">'
                       '<circle cx=".75" cy=".75" r=".42"/><circle cx="2.25" cy="2.25" r=".42"/></pattern></defs></svg>')
    return (f'<div class="kdefs" aria-hidden="true">{"".join(defs)}</div>' if defs else "") + "".join(x for _, x in items)


FILL_JS = ("<script>(function(){function f(n){var b=document.querySelector('.kbar'),fr=document.querySelector('#kmain .kframe'),"
           "k=document.querySelector('#kmain .kfill');if(!b||!fr||!k)return;var v=k.querySelectorAll('.kpv'),x=k.querySelector('.kfrule'),i,pick=null,ph=0;"
           "k.style.height='0px';k.style.paddingTop='0px';fr.className=fr.className.replace(/ ksqz/g,'');var d0=fr.querySelectorAll('.kdrop1,.kdrop2,.kdrop3');for(i=0;i<d0.length;i++)d0[i].style.display='';var kd=fr.children;for(i=0;i<kd.length;i++)if(kd[i]!==k)kd[i].style.removeProperty('margin-bottom');var op0=document.querySelectorAll('#kmain .kopt');for(i=0;i<op0.length;i++)op0[i].style.display='none';for(i=0;i<v.length;i++)v[i].style.display='none';if(x)x.style.display='none';"
           "function room(){return Math.floor(b.getBoundingClientRect().top-fr.getBoundingClientRect().bottom);}"
           "var c=document.querySelector('#kmain .kcentre'),ca=c?c.querySelectorAll('.kca'):[],cp=null,chh=0;"
           "if(ca.length){for(i=0;i<ca.length;i++)ca[i].style.display='none';c.style.display='none';var fr0=room()-7,cap=(fr0-132>=63)?132:fr0;"
           "for(i=0;i<ca.length;i++){var q=+ca[i].getAttribute('data-h');if(!cp||(q<=cap&&q>chh)){cp=ca[i];chh=q;}}"
           "cp.style.display='block';c.style.height=chh+'px';c.style.display='block';}"
           "var dl,lv;for(lv=1;lv<=3&&room()<0;lv++){if(lv==1&&!/ksqz/.test(fr.className)){fr.className+=' ksqz';if(room()>=0)break;}"
           "dl=fr.querySelectorAll('.kdrop'+lv);for(i=0;i<dl.length;i++)dl[i].style.display='none';}"
           "var op=document.querySelectorAll('#kmain .kopt');for(i=0;i<op.length;i++){op[i].style.display='block';if(room()<2)op[i].style.display='none';}"
           "var free=room(),rm=free-3;if(free>=12){"
           "for(i=0;i<v.length;i++){var hh=+v[i].getAttribute('data-h');if(hh<=rm&&hh>ph){pick=v[i];ph=hh;}}"
           "if(pick)pick.style.display='block';}"
           "var kids=[],ch=fr.children;for(i=0;i<ch.length;i++){var cc=ch[i];if(cc!==k&&cc.offsetHeight>0&&!/kdefs|ktop/.test(cc.className))kids.push(cc);}"
           "var sp=kids.length?Math.min(8,Math.floor((rm-ph)/kids.length)):0;if(sp>0){for(i=0;i<kids.length;i++)kids[i].style.setProperty('margin-bottom',"
           "(parseFloat(getComputedStyle(kids[i]).marginBottom)+sp)+'px','important');free=room();}"
           "if(pick){k.style.paddingTop='3px';k.style.height=free+'px';}"
           "if(!n){try{document.documentElement.setAttribute('data-kev',String(+new Date()));window.dispatchEvent(new Event('resize'));}catch(e){}setTimeout(function(){"
           "f(1);},260);}else{try{document.documentElement.setAttribute('data-kev',String(+new Date()));window.dispatchEvent(new Event('resize'));}catch(e){}}}"
           "function go(){setTimeout(function(){if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){f(0);});else f(0);},120);}"
           "window.addEventListener('load',go);})();</script>")


def _drop_style(night, salt, letter=""):
    """The drop cap: a historiated initial (the letter on a little engraved river scene, moon and firs)
    from the book engraver, or else set in a guilloche medallion. A per-page p.kdrop:first-letter background."""
    from urllib.parse import quote
    if letter.isalpha():
        try:
            from . import plate_book
            import base64
            sd = (night.toordinal() + sum(map(ord, salt))) % 50 * 4  # seed % 4 == 0: the river ground
            svg = plate_book.initial(letter.upper(), 84, sd)
            url = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
            return ('<style>#kmain .kbody p.kdrop:first-letter{background:#fff url("' + url
                    + '") center/100% 100% no-repeat !important;color:transparent !important;border-color:transparent !important;text-shadow:none !important}</style>')
        except Exception:  # noqa: BLE001
            pass
    rng = engraving.rng_for(night, "drop" + salt)
    g = (engraving.ring(rng, "a", 37, 62) + '<circle r="37" fill="#fff" stroke="#000" stroke-width=".9"/>'
         '<circle r="39.2" fill="none" stroke="#000" stroke-width=".5"/>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="-40 -40 80 80" '
           f'preserveAspectRatio="xMidYMid slice">{g}</svg>')
    url = quote(svg, safe=" =:/,.-")
    return ('<style>#kmain .kbody p.kdrop:first-letter{background:#fff url("data:image/svg+xml,' + url
            + '") center/cover no-repeat !important;text-shadow:1px 0 #fff,-1px 0 #fff,0 1px #fff,0 -1px #fff,1px 1px #fff,-1px -1px #fff,1px -1px #fff,-1px 1px #fff !important}</style>')


def _night_ribbon(w, night, text):
    """A guilloche ribbon, seeded by the night, with tonight's particulars lettered on a tablet at its centre."""
    h, c = 20, w / 2
    tw = min(w - 40, len(re.sub(r"&\w+;", "x", text)) * 4.5 + 30)
    g = (f'<clipPath id="kqc"><rect y="3" width="{_n(w)}" height="14"/></clipPath><g clip-path="url(#kqc)"><g transform="translate(0,3)">'
         + engraving.band(engraving.rng_for(night, "ribbon"), "kqb", w, 14) + '</g></g>'
         f'<path d="M0,2.4H{_n(w)}M0,17.6H{_n(w)}" {K} stroke-width="{W1}"/><path d="M0,.5H{_n(w)}M0,19.5H{_n(w)}" {K} stroke-width="{W0}"/>'
         f'<rect x="{_n(c - tw / 2)}" y="1" width="{_n(tw)}" height="18" rx="9" fill="#fff" {K} stroke-width="{W2}"/>'
         f'<rect x="{_n(c - tw / 2 + 2.6)}" y="3.6" width="{_n(tw - 5.2)}" height="12.8" rx="6.4" fill="none" {K} stroke-width="{W0}"/>'
         + _kanok(c - tw / 2 - 1, 10, .55, 180) + _kanok(c + tw / 2 + 1, 10, .55, 0)
         + f'<text x="{_n(c)}" y="13.4" text-anchor="middle" class="kribt">{text}</text>')
    return _svg(w, h, g, "kribbon")


def ORNAMENTS_BRIDGE_INNER():
    return _vig_bridge().split(">", 1)[1].rsplit("</svg>", 1)[0]


def _kanok_band(w):
    """Lai rot nam: a running stem with kanok flames, white on a cross-hatched lacquer ground."""
    c, h, y = w / 2, 18, 9
    stem = _waves(0, w, y, 2.6, 30)
    flames = ""
    x, i = 6.0, 0
    while x < w:
        up = i % 2 == 0
        # each flame sprouts where the stem crosses its crest, leaning the way the stem runs
        flames += (_kanok(x + 3, y + (1.6 if up else -1.6), .5, -24) if up
                   else _kanok(x + 3, y - 1.6, .5, 24, False).replace("rotate(24)", "rotate(24) scale(1,-1)"))
        x += 15
        i += 1
    g = (f'<rect y="2" width="{_n(w)}" height="14" fill="url(#ke-x)"/>'
         f'<clipPath id="kbc"><rect y="2" width="{_n(w)}" height="14"/></clipPath><g clip-path="url(#kbc)">'
         f'<path d="{stem}" fill="none" stroke="#000" stroke-width="3"/><path d="{stem}" fill="none" stroke="#fff" stroke-width="1.4"/>'
         f'{flames}</g>'
         f'<path d="M0,.8H{_n(w)}M0,17.2H{_n(w)}" {K} stroke-width="{W0}"/><path d="M0,2.4H{_n(w)}M0,15.6H{_n(w)}" {K} stroke-width="{W1}"/>')
    g += (f'<rect x="{_n(c - 14)}" y="1" width="28" height="16" fill="#fff"/>'
          + _kanok(c + 4, y, .55, 0) + _kanok(c - 4, y, .55, flip=True) + _pearl(c, y, 4.4) + _star(c, y, 2.2)
          + f'<path d="M0,.8H{_n(w)}M0,17.2H{_n(w)}" {K} stroke-width="{W0}"/>')
    return _svg(w, h, g, "kband")


def _cartouche(text, w=516):
    """An engraved oval with letter-spaced small caps, kanok finials and acanthus sprays to either side."""
    c, rx = w / 2, 182  # the oval holds the 13 px caps the Kindle stylesheet sets on SVG text
    sprays = (f'<path d="M{_n(c + rx + 14)},15H{_n(w - 8)}" {K} stroke-width="{W0}"/>'
              + _leaf(c + rx + 24, 15, .55, -10) + _leaf(c + rx + 40, 15, .45, 12)
              + f'<circle cx="{_n(w - 5)}" cy="15" r="1.1"/>')
    finial = _kanok(c + rx + 1, 15, 1.0, 0)
    side = sprays + finial
    g = (side + f'<g transform="translate({_n(w)},0) scale(-1,1)">{side}</g>'
         f'<ellipse cx="{_n(c)}" cy="15" rx="{rx}" ry="13" fill="#fff" {K} stroke-width="{W2}"/>'
         f'<ellipse cx="{_n(c)}" cy="15" rx="{rx - 3}" ry="10" fill="none" {K} stroke-width="{W0}"/>'
         f'<text x="{_n(c)}" y="18.4" text-anchor="middle" class="kcart" font-size="8.6" font-weight="600" letter-spacing="1.2">{text}</text>')
    return _svg(w, 30, g, "kcartouche")


def _vig_news():
    """The day: the evening paper laid flat beside a cup of coffee on its saucer. 220 x 56."""
    tl, tr, br, bl = (52, 6), (150, 6), (160, 50), (42, 50)

    def at(f, y):  # x on a column rule a fraction f across the sheet, at height y
        t = (y - 6) / 44
        return tl[0] + (bl[0] - tl[0]) * t + ((tr[0] + (br[0] - tr[0]) * t) - (tl[0] + (bl[0] - tl[0]) * t)) * f
    sheet = f"M{tl[0]},{tl[1]}L{tr[0]},{tr[1]}L{br[0]},{br[1]}L{bl[0]},{bl[1]}Z"
    under = (f'<path d="M{bl[0] + 4},{bl[1] + 3}L{br[0] + 4},{br[1] + 3}L{tr[0] + 4},{tr[1] + 3}L{tr[0]},{tr[1]}L{br[0]},{br[1]}L{bl[0]},{bl[1]}Z" '
             f'fill="url(#ke-d)" {K} stroke-width="{W0}"/>')
    cols = "".join(f'M{_n(at(f, 25))},25L{_n(at(f, 48))},48' for f in (1 / 3, 2 / 3))
    lines = ""
    for y in [x / 10 for x in range(270, 480, 22)]:
        for c0, c1 in ((0, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 1)):
            if c0 == 0 and y < 38:  # the photograph
                continue
            lines += f'M{_n(at(c0, y) + 2)},{_n(y)}L{_n(at(c1, y) - 2)},{_n(y)}'
    photo = (f'<path d="M{_n(at(0, 26) + 2)},26L{_n(at(1 / 3, 26) - 2)},26L{_n(at(1 / 3, 36) - 2)},36L{_n(at(0, 36) + 2)},36Z" '
             f'fill="url(#ke-x)" {K} stroke-width=".45"/>')
    head = (f'<text x="101" y="15.4" text-anchor="middle" class="ksm">The Evening News</text>'
            f'<path d="M{_n(at(0, 18) + 1)},18L{_n(at(1, 18) - 1)},18M{_n(at(0, 20.4) + 1)},20.4L{_n(at(1, 20.4) - 1)},20.4" {K} stroke-width=".5"/>'
            f'<path d="M{_n(at(1 / 3, 23.2) + 2)},23.2L{_n(at(1, 23.2) - 3)},23.2" {K} stroke-width="1.5"/>')
    paper = (under + f'<path d="{sheet}" fill="#fff" {K} stroke-width="{W1}" stroke-linejoin="round"/>' + head + photo
             + f'<path d="{cols}" {K} stroke-width=".4"/><path d="{lines}" {K} stroke-width=".45" stroke-dasharray="7 1.2 4 1.2 9 1.2"/>')
    cup = (f'<ellipse cx="186" cy="48" rx="22" ry="5" fill="url(#ke-s2)" {K} stroke-width="{W0}"/>'
           f'<ellipse cx="186" cy="47" rx="12" ry="2.4" fill="none" {K} stroke-width=".4"/>'
           f'<path d="M172,24H200L197,42C196.5,44.5 192,45.6 186,45.6C180,45.6 175.5,44.5 175,42Z" fill="#fff" {K} stroke-width="{W1}"/>'
           f'<path d="M190,25H199L196.4,42C195.8,43.8 193,44.8 190,45Z" fill="url(#ke-h)"/>'
           f'<path d="M199.4,28C205,27 207,31 205,35C203.5,37.5 200,38 197.6,37.4" fill="none" {K} stroke-width="{W1}"/>'
           f'<ellipse cx="186" cy="24" rx="14" ry="2.6" fill="url(#ke-x)" {K} stroke-width="{W0}"/>'
           f'<path d="M181,19C178,15 183,12 180,7M187,19C184,14 190,11 186,4M193,19C190,15 195,13 192,9" fill="none" {K} stroke-width=".5"/>')
    spoon = f'<path d="M206,50.5L216,52" {K} stroke-width="1.2" stroke-linecap="round"/><ellipse cx="204" cy="50" rx="3" ry="1.3" fill="#fff" {K} stroke-width="{W0}"/>'
    return _svg(220, 56, f'<g transform="translate(-19,0)">{paper}{cup}{spoon}</g>', "kvig")


def _vig_bridge():
    """Close to home: the St. Johns Bridge's Gothic towers over the Willamette, Forest Park behind. 220 x 56."""
    hill = (f'<path d="M0,30C30,22 60,20 90,24C120,28 160,18 220,22V44H0Z" fill="url(#ke-s)" {K} stroke-width="{W0}"/>'
            + "".join(_fir(x, 30 - (x % 13) * .3, 8 + x % 5) for x in range(6, 220, 9)))

    def tower(x):
        return (f'<path d="M{x - 4},44V10L{x - 2},4L{x},0L{x + 2},4L{x + 4},10V44Z" fill="#fff" {K} stroke-width="{W1}"/>'
                f'<path d="M{x - 2.4},38V14Q{x - 2.4},10 {x},8Q{x + 2.4},10 {x + 2.4},14V38" fill="url(#ke-d)" {K} stroke-width=".4"/>'
                f'<path d="M{x - 4},24H{x + 4}M{x - 4},32H{x + 4}" stroke="#fff" stroke-width=".9"/>')
    cables = (f'<path d="M0,34Q40,30 66,8M66,8Q110,64 154,8M154,8Q180,30 220,34" fill="none" {K} stroke-width="{W1}"/>'
              + "".join(f'<path d="M{x},{_n(y)}V38" {K} stroke-width=".35"/>' for x, y in
                        [(x, 8 + 28 * (1 - ((x - 110) / 44) ** 2) * .98) for x in range(72, 150, 6)]))
    deck = f'<path d="M0,38H220" {K} stroke-width="{W2}"/><path d="M0,40.4H220" {K} stroke-width="{W0}"/>'
    water = f'<rect y="44" width="220" height="12" fill="#fff"/>' + _water(0, 220, 44, 56)
    return _svg(220, 56, hill + cables + tower(66) + tower(154) + deck + water, "kvig")


def _vig_weather(kind):
    """Tomorrow: three Douglas firs under the day's weather. 128 x 84."""
    g = ""
    if kind in ("sun", "partly"):
        cx, cy, r = (64, 26, 11) if kind == "sun" else (46, 22, 9)
        rays = ""
        import math as _m
        for i in range(24):
            a = 2 * _m.pi * i / 24
            r2 = r + (11 if i % 2 == 0 else 6)
            rays += f"M{_n(cx + (r + 3) * _m.cos(a))},{_n(cy + (r + 3) * _m.sin(a))}L{_n(cx + r2 * _m.cos(a))},{_n(cy + r2 * _m.sin(a))}"
        g += f'<path d="{rays}" {K} stroke-width="{W0}"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#ke-s)" {K} stroke-width="{W1}"/>'
    if kind in ("partly", "cloud", "rain", "snow", "storm", "fog"):
        ox, oy = (24, -2) if kind == "partly" else (14, -10 if kind in ("rain", "snow", "storm") else -6)
        cloud = ("M20,46C10,46 8,34 17,32C16,22 28,18 34,24C38,14 54,14 57,26C66,24 72,32 68,40C72,42 70,46 66,46Z")
        g += (f'<g transform="translate({ox},{oy})"><clipPath id="kwc"><path d="{cloud}"/></clipPath>'
              f'<path d="{cloud}" fill="#fff"/><g clip-path="url(#kwc)"><rect x="0" y="36" width="80" height="12" fill="url(#ke-h)"/>'
              f'<rect x="0" y="40" width="80" height="8" fill="url(#ke-x)"/></g>'
              f'<path d="{cloud}" fill="none" {K} stroke-width="{W1}"/>'
              f'<path d="M24,30C28,27 33,28 35,31M41,25C46,22 52,24 53,29" fill="none" {K} stroke-width=".45"/></g>')
    if kind == "rain":
        g += f'<path d="{"".join(f"M{30 + 8 * i},{40 + (i % 2) * 4}l-3,8" for i in range(10))}" {K} stroke-width="{W0}" stroke-linecap="round"/>'
    if kind == "storm":
        g += f'<path d="M62,36L54,50H60L55,62L68,46H62L67,36Z" fill="url(#ke-d)" {K} stroke-width="{W0}"/>'
    if kind == "snow":
        g += "".join(_star(30 + 9 * i, 42 + (i % 3) * 5, 2.2) for i in range(9))
    if kind == "fog":
        g += "".join(f'<path d="M{8 + (i % 2) * 10},{44 + i * 4}H{120 - (i % 3) * 8}" {K} stroke-width="{W0}" stroke-dasharray="14 3 6 3"/>' for i in range(4))
    if kind == "clear-night":
        g += _moon_shape(64, 24, 10, 30, True, "kwm")
    ground = (f'<path d="M0,80C30,77 60,79 128,78" fill="none" {K} stroke-width="{W0}"/>'
              f'<path d="M4,82H40M50,82.5H100M106,82H124" {K} stroke-width=".4"/>')
    firs = _fir(16, 80, 46) + _fir(108, 80, 52) + _fir(122, 80, 34) + _fir(4, 80, 30)
    ferns = "".join(f'<path d="M{x},80Q{x + 4},72 {x + 9},70M{x + 2},77l2,-3M{x + 4},75l2,-4M{x + 6},73l2,-3" fill="none" {K} stroke-width=".45"/>'
                    for x in (30, 84))
    return _svg(128, 84, g + firs + ferns + ground, "kvig kvwx")


def _vig_listening():
    """The poem: a dog asleep on the rug beside a record player. 170 x 56."""
    rug = (f'<ellipse cx="62" cy="48" rx="46" ry="6.5" fill="url(#ke-p)" {K} stroke-width="{W0}"/>'
           f'<ellipse cx="62" cy="48" rx="41" ry="4.4" fill="none" {K} stroke-width=".4"/>'
           + "".join(f'<path d="M{_n(16 + 4.6 * i)},{_n(48 + (6.6 if 2 < i < 18 else 4))}v2" {K} stroke-width=".4"/>' for i in range(21)))
    dog = f'<g transform="translate(28,8) scale(1.6)">' + _subj_dog().replace('<ellipse cx="20" cy="31" rx="15" ry="3" fill="url(#ke-s2)" stroke="#000" stroke-width=".4"/>', "") + "</g>"
    table = (f'<path d="M116,30H166V34H116Z" fill="url(#ke-h)" {K} stroke-width="{W0}"/>'
             f'<path d="M120,34V54M162,34V54M118,54H124M160,54H166" {K} stroke-width="{W1}"/>'
             f'<path d="M120,46H162" {K} stroke-width="{W0}"/>'
             + "".join(f'<rect x="{x}" y="38" width="2.2" height="16" fill="#fff" {K} stroke-width=".4"/>' for x in range(124, 160, 3)))
    player = (f'<path d="M118,22H164V30H118Z" fill="#fff" {K} stroke-width="{W1}"/>'
              f'<ellipse cx="136" cy="22" rx="15" ry="3.2" fill="url(#ke-d)" {K} stroke-width="{W0}"/>'
              f'<ellipse cx="136" cy="22" rx="4" ry=".9" fill="#fff" {K} stroke-width=".4"/>'
              f'<path d="M158,20V18L146,21.6" fill="none" {K} stroke-width="{W1}"/><circle cx="158" cy="18.6" r="1.6" fill="#fff" {K} stroke-width="{W0}"/>')
    notes = (f'<path d="M100,12v-7l6,-1.5v7" fill="none" {K} stroke-width="{W0}"/>'
             f'<ellipse cx="98.8" cy="12.2" rx="1.6" ry="1.1"/><ellipse cx="104.8" cy="10.8" rx="1.6" ry="1.1"/>'
             f'<path d="M88,18v-6" {K} stroke-width="{W0}"/><ellipse cx="86.8" cy="18.2" rx="1.6" ry="1.1"/>')
    return _svg(170, 56, rug + dog + table + player + notes, "kvig")


def _crane(x, y, s=1.0, flip=False):
    """A sandhill crane in flight, seen from the side: neck straight out, legs trailing, wings raised in a V."""
    sx = -s if flip else s
    return (f'<g transform="translate({_n(x)},{_n(y)}) scale({_n(sx)},{_n(s)})">'
            f'<path d="M-7,0C-4,-2 3,-2.2 7,-1L16,-2.2L18.6,-2.6L16.4,-1.4L7.4,.6C3,2 -4,2 -7,0Z" fill="url(#ke-x)" {K} stroke-width=".5"/>'
            f'<path d="M17.4,-2.5L21,-2.2" {K} stroke-width=".6"/>'
            f'<path d="M-1,-1.2C-4,-7 -9,-12 -16,-14C-11,-9 -7,-4 -4,-.8Z" fill="#fff" {K} stroke-width="{W0}"/>'
            f'<path d="M-3,-1.6C-6,-6 -10,-10 -15,-12.6M-2.4,-1.2C-5,-5 -8,-8 -12,-10" fill="none" {K} stroke-width=".35"/>'
            f'<path d="M1,-1.6C1,-7 3,-12 7,-16C5,-10 4.6,-5 4,-1Z" fill="url(#ke-h)" {K} stroke-width="{W0}"/>'
            f'<path d="M-7,.2L-19,1.6M-7,.6L-19,2.6" {K} stroke-width=".5"/></g>')


def _vig_goodnight(lit=36, waxing=True):
    """The close: the moon over Sauvie Island, cranes crossing, a guilloche rosette behind the moon. 240 x 140."""
    halo = f'<g>{_rosette(152, 46, 15, 22, 30, .4)}</g><circle cx="152" cy="46" r="20" fill="#fff"/>'
    moon = _moon_shape(152, 46, 17, lit, waxing, "kgm", dark="url(#ke-s)")
    stars = "".join(_star(x, y, r) for x, y, r in ((40, 30, 3.2), (66, 16, 2), (92, 40, 2.4), (210, 24, 2.6), (196, 62, 1.6),
                                                 (28, 58, 1.6), (110, 14, 1.6), (226, 50, 1.4)))
    dust = "".join(f'<circle cx="{(i * 37) % 236 + 2}" cy="{(i * 23) % 70 + 4}" r=".5"/>' for i in range(28))
    cranes = _crane(58, 64, 1.15) + _crane(92, 52, .9) + _crane(112, 70, .75)
    island = (f'<path d="M0,98C20,96 40,94 60,95C70,92 76,86 82,88C88,84 96,86 100,90C110,88 120,92 132,92C150,92 170,95 196,96'
              f'C214,97 228,96 240,97V104H0Z" fill="url(#ke-x)" {K} stroke-width="{W0}"/>'
              + "".join(f'<path d="M{x},96C{x - 3},90 {x - 2},{82 + (x % 7)} {x + 1},{80 + (x % 5)}C{x + 5},{82 + (x % 6)} {x + 5},90 {x + 2},96Z" '
                        f'fill="url(#ke-d)" {K} stroke-width=".45"/>' for x in (66, 74, 82, 90, 98, 106, 116)))
    hood = _hood(206, 96, .45)
    water = f'<rect y="100" width="240" height="40" fill="#fff"/><path d="M0,100H240" {K} stroke-width="{W0}"/>' + _water(0, 240, 100, 138, 152)
    oval = "M120,2C186,2 238,32 238,70C238,108 186,138 120,138C54,138 2,108 2,70C2,32 54,2 120,2Z"
    g = (f'<clipPath id="kgo"><path d="{oval}"/></clipPath><g clip-path="url(#kgo)">'
         f'<rect width="240" height="140" fill="url(#ke-s2)"/>{dust}{halo}{moon}{stars}{cranes}{hood}{island}{water}</g>'
         f'<path d="{oval}" fill="none" {K} stroke-width="{W2}"/>'
         f'<ellipse cx="120" cy="70" rx="122.5" ry="70.5" fill="none" {K} stroke-width="{W0}" stroke-dasharray="1 2.4"/>')
    return _svg(246, 142, f'<g transform="translate(3,1)">{g}</g>', "kvig kgn")


# ---- the light frame for text pages, rope boxes, the head band ---------------------------------

def _lite_strips():
    """The text pages' frame: the border family's lighter cousin, a rule, a rope band and a hairline. 9 px deep."""
    h = (f'<path d="M0,.6H9999" {K} stroke-width="{W1}"/><path d="M0,2.2H9999M0,8.4H9999" {K} stroke-width="{W0}"/>'
         )
    v = (f'<path d="M.6,0V9999" {K} stroke-width="{W1}"/><path d="M2.2,0V9999M8.4,0V9999" {K} stroke-width="{W0}"/>'
         )
    return (f'<svg class="kfs kls-t" aria-hidden="true">{h}</svg><svg class="kfs kls-b" aria-hidden="true">{h}</svg>'
            f'<svg class="kfs kls-l" aria-hidden="true">{v}</svg><svg class="kfs kls-r" aria-hidden="true">{v}</svg>')


def _lite_corner(c):
    """A 30 px corner piece for the light frame: a pearl rosette in a square, acanthus running both ways."""
    fx, fy = c[1] == "r", c[0] == "b"
    m = f"translate({30 if fx else 0},{30 if fy else 0}) scale({-1 if fx else 1},{-1 if fy else 1})"
    g = (f'<rect x="0" y="0" width="17" height="17" fill="#fff" {K} stroke-width="{W1}"/>'
         f'<rect x="2" y="2" width="13" height="13" fill="url(#ke-gh)" {K} stroke-width="{W0}"/>'
         + _rosette(8.5, 8.5, 2.4, 3.6, 12, .35) + f'<circle cx="8.5" cy="8.5" r="1.3" fill="#fff" {K} stroke-width=".4"/>'
         + _leaf(18.5, 6.4, .5, -6) + f'<g transform="matrix(0 1 1 0 0 0)">{_leaf(18.5, 6.4, .5, -6)}</g>')
    return _fix(f'<svg class="korn kround kround-{c}" width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">'
                f'<g transform="{m}">{g}</g></svg>')


def _rope_box():
    """Herringbone inlay around a small box (the Next note, the sources line)."""
    h = (f'<path d="M0,.5H9999M0,5.5H9999" {K} stroke-width="{W0}"/><rect x="0" y="1" width="100%" height="4" fill="url(#ke-hb)"/>')
    v = (f'<path d="M.5,0V9999M5.5,0V9999" {K} stroke-width="{W0}"/><rect x="1" y="0" width="4" height="100%" fill="url(#ke-hb-v)"/>')
    return (f'<svg class="kfs kbx-t" aria-hidden="true">{h}</svg><svg class="kfs kbx-b" aria-hidden="true">{h}</svg>'
            f'<svg class="kfs kbx-l" aria-hidden="true">{v}</svg><svg class="kfs kbx-r" aria-hidden="true">{v}</svg>')


def _head_band(label, w=528):
    """The head of every text page: a kanok flame band on cross-hatched lacquer, the kicker in a
    guilloche-bordered tablet at its centre."""
    c = w / 2
    tw = min(w - 60, len(re.sub(r"&\w+;", "x", label)) * 10.6 + 44)
    band = _kanok_band(w).split(">", 1)[1].rsplit("</svg>", 1)[0]
    g = (f'<g transform="translate(0,4)">{band}</g>'
         f'<rect x="{_n(c - tw / 2)}" y="0" width="{_n(tw)}" height="26" rx="3" fill="#fff" {K} stroke-width="{W2}"/>'
         f'<rect x="{_n(c - tw / 2 + 3)}" y="3" width="{_n(tw - 6)}" height="20" rx="1.5" fill="url(#ke-gh)" {K} stroke-width="{W0}"/>'
         f'<rect x="{_n(c - tw / 2 + 12)}" y="5.6" width="{_n(tw - 24)}" height="14.8" fill="#fff" {K} stroke-width=".4"/>'
         + _kanok(c - tw / 2 - 1, 13, .7, 180) + _kanok(c + tw / 2 + 1, 13, .7, 0)
         + f'<text x="{_n(c)}" y="17.6" text-anchor="middle" class="khb">{label}</text>')
    return _svg(w, 26, g, "khb")


def _subj_lotus():
    """A lotus open on the water: three ranks of petals, the far ones hatched."""
    pet = "M0,0C4,-6 4,-14 0,-20C-4,-14 -4,-6 0,0Z"
    g = "".join(f'<path d="{pet}" transform="translate(20,30) rotate({a}) scale({sc})" fill="{f}" {K} stroke-width="{W0}"/>'
                for a, sc, f in ((-72, .62, "url(#ke-h)"), (72, .62, "url(#ke-h)"), (-40, .8, "url(#ke-s)"), (40, .8, "url(#ke-s)"),
                                 (-16, .92, "#fff"), (16, .92, "#fff"), (0, 1, "#fff")))
    g += (f'<path d="M20,30V13M18,28C18.6,22 18.6,18 18.2,14M22,28C21.4,22 21.4,18 21.8,14" fill="none" {K} stroke-width=".35"/>'
          f'<path d="M5,32.5H35M9,35H31M13,37.4H27" {K} stroke-width=".45"/>'
          f'<ellipse cx="9" cy="31.4" rx="5" ry="1.4" fill="url(#ke-x)" {K} stroke-width=".4"/>')
    return g


def _medallion(subject, cid, size=30, sub_scale=.62):
    """A small engraved medallion for the cover's flanks and sides."""
    c = size / 2
    off = c - 20 * sub_scale
    return _svg(size, size, f'<circle cx="{c}" cy="{c}" r="{_n(c - .8)}" fill="#fff" {K} stroke-width="{W2}"/>'
                f'<circle cx="{c}" cy="{c}" r="{_n(c - 3)}" fill="none" {K} stroke-width="{W0}" stroke-dasharray="1 1.6"/>'
                f'<clipPath id="{cid}"><circle cx="{c}" cy="{c}" r="{_n(c - 4)}"/></clipPath>'
                f'<g clip-path="url(#{cid})"><g transform="translate({_n(off)},{_n(off)}) scale({sub_scale})">{subject}</g></g>',
                "kmed")


def _vig_drums():
    """The day, second story: a jazz kit, the bass drum's head engraved with a guilloche rosette. 220 x 56."""
    def drum(cx, top, h, rx, ry, tone):
        return (f'<path d="M{cx - rx},{top}V{top + h}A{rx},{ry} 0 0 0 {cx + rx},{top + h}V{top}Z" fill="{tone}" {K} stroke-width="{W0}"/>'
                f'<path d="M{cx - rx},{top + 2}A{rx},{ry} 0 0 0 {cx + rx},{top + 2}M{cx - rx},{top + h - 1.4}A{rx},{ry} 0 0 0 {cx + rx},{top + h - 1.4}" fill="none" {K} stroke-width=".45"/>'
                f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="#fff" {K} stroke-width="{W1}"/>')
    hat = (f'<path d="M44,15V54M44,48L36,54M44,48L52,54" {K} stroke-width="{W0}"/>'
           f'<ellipse cx="44" cy="16.6" rx="13" ry="2" fill="#fff" {K} stroke-width="{W0}"/><ellipse cx="44" cy="14" rx="13" ry="2.2" fill="url(#ke-d)" {K} stroke-width="{W0}"/>')
    ride = (f'<path d="M180,10V54M180,48L172,54M180,48L188,54" {K} stroke-width="{W0}"/>'
            f'<ellipse cx="180" cy="9" rx="17" ry="3" transform="rotate(-8 180 9)" fill="url(#ke-s2)" {K} stroke-width="{W0}"/>'
            f'<circle cx="180" cy="9" r="1.4" fill="#fff" {K} stroke-width=".4"/>')
    bass = (f'<circle cx="110" cy="35" r="19" fill="#fff" {K} stroke-width="{W1}"/><circle cx="110" cy="35" r="16.4" fill="none" {K} stroke-width="{W0}"/>'
            + _rosette(110, 35, 5, 7.4, 18, .35) + f'<circle cx="110" cy="35" r="2" fill="#fff" {K} stroke-width=".45"/>'
            + "".join(f'<circle cx="{_n(110 + 17.7 * math.cos(a))}" cy="{_n(35 + 17.7 * math.sin(a))}" r=".8"/>' for a in [i * math.pi / 5 for i in range(10)]))
    snare = drum(70, 30, 7, 12, 3.2, "url(#ke-s)") + f'<path d="M70,40.5V54M70,46L62,54M70,46L78,54" {K} stroke-width="{W0}"/>'
    toms = drum(97, 11, 8, 9, 2.6, "url(#ke-h)") + drum(123, 11, 8, 9, 2.6, "url(#ke-h)") + f'<path d="M104,20L110,16L116,20" fill="none" {K} stroke-width="{W0}"/>'
    floor = drum(151, 29, 18, 12, 3.2, "url(#ke-h)") + f'<path d="M141,49L139,54M161,49L163,54" {K} stroke-width="{W0}"/>'
    sticks = f'<path d="M58,22L80,29M82,22L62,29" {K} stroke-width="1.2" stroke-linecap="round"/>'
    ground = f'<path d="M20,54.4H200" {K} stroke-width="{W0}"/><path d="M30,55.6H190" {K} stroke-width=".35" stroke-dasharray="6 2"/>'
    return _svg(220, 56, ground + hat + ride + toms + floor + bass + snare + sticks, "kvig")


def _vig_marsh():
    """The day, third story: sandhill cranes over the Sauvie Island marsh, a heron in the reeds. 220 x 56."""
    hills = (f'<path d="M120,36C140,30 160,28 180,30C196,31 210,28 220,29V44H120Z" fill="url(#ke-s)" {K} stroke-width="{W0}"/>'
             + "".join(_fir(x, 38 - (x % 7) * .3, 10 + x % 6) for x in range(138, 220, 8)))
    shore = f'<path d="M0,44H220" {K} stroke-width="{W0}"/>' + _water(0, 220, 44, 56)
    reeds = "".join(f'<path d="M{x},46C{x - 1},40 {x + 1},{36 - x % 5} {x + 3},{32 - x % 7}" fill="none" {K} stroke-width=".5"/>'
                    for x in range(58, 100, 4))
    heron = f'<g transform="translate(12,0) scale(1.3)">{_subj_heron()}</g>'
    cranes = _crane(78, 14, 1.0) + _crane(108, 8, .8) + _crane(130, 18, .68)
    sun = _moon_shape(196, 12, 6, 30, True, "kmm", dark="url(#ke-s)")
    return _svg(220, 56, hills + shore + reeds + heron + cranes + sun, "kvig")


ORNAMENTS = {
    "defs": _defs(),
    "divider": _divider(),
    "tail": _tailpiece(),
    "asterism": _asterism(),
    "frame": _frame_strips(),
    "news": _vig_news(),
    "bridge": _vig_bridge(),
    "listening": _vig_listening(),
    "goodnight": _vig_goodnight(),
    "drums": _vig_drums(),
    "marsh": _vig_marsh(),
    "lite": _lite_strips() + "".join(_lite_corner(c) for c in ("tl", "tr", "bl", "br")),
    "box": _rope_box(),
    "roundels": {k: _roundel(f(), f"kr{k}", k) for k, f in
                 (("tl", _subj_dog_head), ("tr", _subj_drums), ("bl", _subj_heron), ("br", _subj_record))},
    "rosettes": {k: _roundel(_subj_rosette(), f"kq{k}", k) for k in ("tl", "tr", "bl", "br")},
}


ALARM = re.compile(r"\b(breaking|urgent|shocking|slams?|chaos|deadly|crisis|developing story|live (?:updates|coverage|blog)|exclusive|horrific|massive)\b", re.I)
# Stories that make poor bedtime reading unless they're the day's biggest by far.
GRAPHIC = re.compile(r"\b(kill(s|ed|ing)?|dead|deaths?|dies|died|murder\w*|shoot\w*|shot|stab\w*|buried alive|rape\w*|"
                     r"abuse\w*|massacre|bodies|body|corpse|hit-and-run|gunman|assault\w*|torture\w*|molest\w*|child porn\w*|"
                     r"overdose\w*|suicide|injur\w*|wounded|trapped|bomb\w*|attack\w*)\b", re.I)
# Gossip and personal scandal: not for bedtime unless it's the day's biggest story.
GOSSIP = re.compile(r"\b(relationship|affair|scolded|scolds|feuds?|feuding|cheated on|cheating on|divorc\w*|"
                    r"breakup|break-up|girlfriend|boyfriend|ex-wife|ex-husband|romance|snubs?|snubbed|"
                    r"slept with|sex scandal|leaked texts)\b", re.I)
ROUND = [10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
PREFER = ["AP", "Associated Press", "Reuters", "NPR", "PBS NewsHour", "BBC", "The Guardian", "The New York Times",
          "The Washington Post", "Axios", "CBS News", "ABC News", "NBC News", "Politico", "Al Jazeera"]


def outlets_line(st):
    n = st.get("coverage") or 0
    names = [st.get("source")] + [a.get("source") if isinstance(a, dict) else a for a in st.get("also") or []]
    names = [x for x in dict.fromkeys(names) if x]
    names.sort(key=lambda x: PREFER.index(x) if x in PREFER else 99)
    top = names[:3]
    if n <= 1 or not top:
        return f"Source: {E(st.get('source') or 'news reports')}."
    listed = top[0] if len(top) == 1 else ", ".join(top[:-1]) + " and " + top[-1]
    if n < 10:
        return f"Covered by {n} outlets, including {E(listed)}." if n > len(top) else f"Covered by {E(listed)}."
    about = min(ROUND, key=lambda r: abs(r - n))
    return f"Covered by about {about} outlets, including {E(listed)}."


def _fresh(ev, night, now):
    if not ev or ev.get("date") != night.isoformat():
        return False
    try:
        written = dt.datetime.fromisoformat(ev["written_at"].replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return False
    return now - written < dt.timedelta(hours=10)


def _recent(items, now, hours=18):
    out = []
    for it in items or []:
        try:
            t = dt.datetime.fromisoformat(it["utc"].replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            t = now
        if now - t <= dt.timedelta(hours=hours):
            out.append(it)
    return out


def smart(t):
    """Typeset plain copy: curly quotes and apostrophes, en dashes for spaced hyphens."""
    if not isinstance(t, str):
        return t
    t = re.sub(r"(\w)'(\w)", "\\1\u2019\\2", t)
    t = re.sub(r"(^|[\s(\[\u2014\u2013])'", "\\1\u2018", t)
    t = t.replace("'", "\u2019")
    t = re.sub(r'(^|[\s(\[\u2014\u2013])"', "\\1\u201c", t)
    t = t.replace('"', "\u201d")
    return re.sub(r" -{1,2} ", " \u2013 ", t)


def _from_feed(it, major=False):
    summary = (it.get("summary") or "").strip()
    return {**it, "headline": re.sub(r"\s+", " ", it.get("title") or "").strip(), "paras": [summary] if summary else [],
            "next": None, "major": major}


def pick_feed(items, n):
    """Without the local model: the most-covered stories, leaving out graphic ones unless one is far bigger than the rest."""
    items = sorted(items, key=lambda x: -(x.get("coverage") or 0))
    out = []
    for k, it in enumerate(items):
        text = f"{it.get('title', '')} {it.get('summary', '')}"
        nxt = items[k + 1].get("coverage", 0) if k + 1 < len(items) else 0
        major = (it.get("coverage") or 0) >= max(6, 2 * nxt) and k == 0
        if ALARM.search(text) or len((it.get("title") or "").split()) > 14:
            continue
        if (GRAPHIC.search(text) or GOSSIP.search(text)) and not major:
            continue
        out.append(_from_feed(it, major))
        if len(out) >= n:
            break
    return out


def _from_model(st):
    paras = [p for p in (st.get("happened"), st.get("tonight")) if p]
    return {**st, "paras": paras, "next": st.get("next")}


def stories(d, ev, night, now):
    news = d.get("news") or {}
    if _fresh(ev, night, now) and ev.get("stories"):
        big = [_from_model(s) for s in ev["stories"]][:3]
        loc = _from_model(ev["local"]) if ev.get("local") else None
        return big, loc, True
    big = pick_feed(_recent(news.get("big"), now), 3)
    loc = pick_feed(_recent(news.get("local"), now, 24), 1)
    return big, (loc[0] if loc else None), False


FRAME_W = 522  # the cover's measure inside its frame: 570 less the frame and its padding

ROMAN = ["I", "II", "III", "IV", "V"]


def poem_html(p):
    """The poem as a bookplate. Short poems get the full plate (frame, vignette, tailpiece); longer ones
    shed ornament, then a size of type, so the poem always sits on one screen."""
    stanzas = [s for s in p["text"].strip().split("\n\n") if s.strip()]
    nlines = sum(len(s.strip().split("\n")) for s in stanzas)
    size = nlines + (len(stanzas) - 1) / 2  # a stanza gap is half a line
    body = '<div class="gap"></div>'.join("".join(f"<span>{E(smart(line.strip()))}</span>" for line in s.strip().split("\n")) for s in stanzas)
    by = E(p["poet"]) + (f" &middot; {p['year']}" if p.get("year") else "")
    text = (f'<span class="poem-title">{E(p["title"])}</span><span class="poem-by">{by}</span>'
            f'<div class="poem-text">{body}</div>')
    return f'<div class="kplate{" klong" if size > 20 else ""}"><div class="kpoem">{text}</div></div>'


def _corner_blocks():
    """Small pearl-inlay blocks for the corners of the poem's plate (14 x 14)."""
    blk = (f'<rect width="14" height="14" fill="#fff"/><rect x="1" y="1" width="12" height="12" fill="url(#ke-p)" {K} stroke-width="{W1}"/>'
           f'<rect x="4" y="4" width="6" height="6" fill="#fff" {K} stroke-width="{W0}" transform="rotate(45 7 7)"/>' + _star(7, 7, 2.2))
    return "".join(_fix(f'<svg class="korn kround kround-{c}" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">{blk}</svg>')
                   for c in ("tl", "tr", "bl", "br"))


def moon_phase(night):
    """The moon's phase at 9 pm, up or not: (per cent lit, waxing, name), or None without ephem."""
    try:
        import ephem
    except ImportError:
        return None
    o = ephem.Observer()
    o.date = ephem.Date(dt.datetime.combine(night, dt.time(21), TZ).astimezone(dt.timezone.utc).replace(tzinfo=None))
    m = ephem.Moon(o)
    lit = round(m.phase)
    waxing = (o.date - ephem.previous_new_moon(o.date)) < 14.77
    if lit < 3:
        name = "New moon"
    elif 45 <= lit <= 55:
        name = "First quarter" if waxing else "Last quarter"
    elif lit > 97:
        name = "Full moon"
    else:
        name = ("Waxing" if waxing else "Waning") + (" crescent" if lit < 50 else " gibbous")
    return lit, waxing, name


AZ = {name: 45 * i for i, name in enumerate(evening.POINTS)}
PEAKS = (("St Helens", 41, .3), ("Adams", 61, .26), ("Mt Hood", 113, .42))  # bearings from Sauvie Island


def sky_chart(planets, mo, phase, night, w=506, h=180):
    """Where to look, as an engraved plate: a panorama from north round through south to north, the
    sky ruled in fine horizontal lines (the engraver's night), the island's treeline and the Cascade
    peaks on the horizon, the planets and moon set in white by direction and height."""
    import random
    y0, top = h - 50, 6
    rnd = random.Random(night.toordinal())

    def X(az):
        return w / 2 + (az - 180) / 180 * (w / 2 - 26)

    def Y(alt):
        return y0 - max(0, min(86, alt)) / 90 * (y0 - top - 8)

    g = [_at._hand("matte", w, y0, 0, 0, style="pearl") or f'<rect x="0" y="0" width="{w}" height="{y0}" fill="url(#ke-rule)"/>']
    # stars: a white gap in the ruling with a black point, a few engraved four-point stars
    for _ in range(70):
        x, y = rnd.uniform(10, w - 10), rnd.uniform(top + 4, y0 - 16)
        r = rnd.choice((.5, .5, .6, .8))
        g.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r + 1.1)}" fill="#fff"/><circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}"/>')
    for _ in range(10):
        x, y, r = rnd.uniform(14, w - 14), rnd.uniform(top + 8, y0 - 28), rnd.uniform(2.4, 3.6)
        g.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r + 1)}" fill="#fff"/>' + _star(x, y, r))
    for alt in (30, 60):
        yy = Y(alt)
        g.append(f'<path d="M30,{_n(yy)}H{w - 30}" stroke="#fff" stroke-width="2.2"/>'
                 f'<path d="M30,{_n(yy)}H{w - 30}" {K} stroke-width=".5" stroke-dasharray="2 3"/>'
                 f'<rect x="3" y="{_n(yy - 9)}" width="50" height="17" fill="#fff" {K} stroke-width=".5"/>'
                 f'<text x="7" y="{_n(yy + 4.5)}" font-size="13">{alt}&deg; up</text>')
    for name, az, sc in PEAKS:
        g.append(_hood(X(az), y0, sc))
        if name != "Adams":  # too close to St Helens to label
            ty = y0 - 40 * sc - 6
            g.append(f'<rect x="{_n(X(az) - 6.8 * len(name) / 2 - 4)}" y="{_n(ty - 12)}" width="{_n(6.8 * len(name) + 8)}" height="16" fill="#fff" {K} stroke-width=".5"/>'
                     f'<text x="{_n(X(az))}" y="{_n(ty)}" font-size="13" text-anchor="middle">{name}</text>')
    # the treeline: cottonwoods and firs along the horizon, low where the peaks stand
    x, tl = 3.0, f"M3,{y0}"
    while x < w - 3:
        step = rnd.uniform(4, 9)
        near = any(abs(x - X(az)) < 44 * sc for _, az, sc in PEAKS)
        crown = y0 - (rnd.uniform(1, 2.5) if near else rnd.uniform(3, 9))
        tl += f"Q{_n(x + step / 2)},{_n(crown - 2)} {_n(min(x + step, w - 3))},{_n(y0 - 1)}"
        x += step
    tl += f"L{w - 3},{y0 + 3}L3,{y0 + 3}Z"
    g.append(f'<path d="{tl}" fill="url(#ke-x)" {K} stroke-width="{W0}"/>')
    g.append(f'<path d="M3,{y0 + 3}H{w - 3}" {K} stroke-width="{W1}"/>' + _water(3, w - 3, y0 + 4, y0 + 22))
    g.append(f'<path d="M3,{y0 + 24}H{w - 3}" {K} stroke-width="{W0}"/>')
    for i, lab in enumerate(["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]):
        xx = X(45 * i)
        g.append(f'<path d="M{_n(xx)},{y0 + 24}v4" {K} stroke-width="{W1}"/>'
                 f'<text x="{_n(xx)}" y="{h - 5}" font-size="13" font-weight="600" text-anchor="middle">{lab}</text>')
    placed = []

    def mark(xx, yy, label, shape):
        lw = 8.3 * len(label) + 10
        anchor, tx = ("end", xx - 15) if xx > w - lw - 30 else ("start", xx + 15)
        x0 = tx - 5 if anchor == "start" else tx - lw + 5
        ty = yy + 4.5
        while any(x0 < a + aw + 4 and a < x0 + lw + 4 and abs(ty - b) < 20 for a, b, aw in placed):
            ty += 20   # a second tag stacks below the first, never over it
        placed.append((x0, ty, lw))
        lead = f'<path d="M{_n(xx)},{_n(yy)}L{_n(x0 if anchor == "start" else x0 + lw)},{_n(ty - 4.5)}" {K} stroke-width=".5"/>' if ty > yy + 5 else ""
        return (lead + shape + f'<rect x="{_n(x0)}" y="{_n(ty - 13)}" width="{_n(lw)}" height="18" fill="#fff" {K} stroke-width="1"/>'
                f'<text x="{_n(tx)}" y="{_n(ty)}" font-size="13" font-weight="600" text-anchor="{anchor}">{label}</text>')

    def at(hour, minute=0):
        return "" if (hour, minute) == (21, 0) else " " + evening.clock(dt.time(hour, minute))
    if mo and phase:
        xx, yy = X(AZ.get(mo["dir"], 180)), Y(mo["alt"])
        g.append(mark(xx, yy, "Moon" + at(mo["hour"]), f'<circle cx="{_n(xx)}" cy="{_n(yy)}" r="11.5" fill="#fff" {K} stroke-width=".45"/>'
                      + _moon_shape(xx, yy, 8.5, phase[0], phase[1], "kcm", dark="url(#ke-n)")))
    for p in planets:
        xx, yy = X(AZ.get(p["dir"], 180)), Y(p["alt"])
        rays = "".join(f'<path d="M{_n(xx)},{_n(yy)}m{dx},{dy}l{dx * 1.2:g},{dy * 1.2:g}" {K} stroke-width="{W0}"/>'
                       for dx, dy in ((0, -6.5), (0, 6.5), (-6.5, 0), (6.5, 0)))
        g.append(mark(xx, yy, p["name"] + at(p["look"].hour, p["look"].minute), f'<circle cx="{_n(xx)}" cy="{_n(yy)}" r="13" fill="#fff"/>' + rays
                      + f'<circle cx="{_n(xx)}" cy="{_n(yy)}" r="4.6" fill="url(#ke-p)" {K} stroke-width="{W1}"/>'
                      f'<circle cx="{_n(xx)}" cy="{_n(yy)}" r="1.3"/>'))
    # no frame of its own: the plaque's moulding is the frame
    return _svg(w, h, "".join(g), "kskychart")


def _moon_plate(lit, waxing, size=120):
    """The moon at its phase in an engraved roundel: a dotted ring set with small stars, the seas stippled,
    the night side in close-ruled engraving so the lit shape reads at any phase."""
    import math as _m
    c, r = size / 2, size / 2 - 13
    ring = "".join(_star(c + (r + 8) * _m.cos(a), c + (r + 8) * _m.sin(a), 2.6) if i % 3 == 0 else
                   f'<circle cx="{_n(c + (r + 8) * _m.cos(a))}" cy="{_n(c + (r + 8) * _m.sin(a))}" r=".7"/>'
                   for i, a in ((i, 2 * _m.pi * i / 36 - _m.pi / 2) for i in range(36)))
    try:  # bulino portrait moon (phase-correct, e-ink safe hatch), its bezel inside the star ring
        from .engraving_eink import engraved_portrait_moon
        ph = _m.acos(max(-1.0, min(1.0, 1 - 2 * lit / 100.0))) / (2 * _m.pi)
        pm = engraved_portrait_moon(ph if waxing else 1 - ph, r - 11, cx=c, cy=c, seed=3,
                                    standalone=False, label=False)
        return _svg(size, size, ring + pm)
    except Exception:
        pass
    return _svg(size, size, ring + _moon_shape(c, c, r, lit, waxing, "kbm", maria=True, dark="url(#ke-n)"))


PAGE_BYTES = 236000  # each page stays under ~240 KB (gzips ~4.5x)
SCREEN = 596  # usable height of a text page, px (618 x 714 less the running head and the bar)


def _tall(text, cpl, lh):
    """Rough height of a paragraph set cpl characters to the line."""
    return math.ceil(len(text or "") / cpl) * lh if text else 0


def wx_kind(wx):
    s = (wx.get("sky") or "").lower()
    if "thunder" in s:
        return "storm"
    if "snow" in s:
        return "snow"
    if any(x in s for x in ("rain", "drizzle", "shower")) or (wx.get("rain_pct") or 0) >= 60:
        return "rain"
    if "fog" in s:
        return "fog"
    if s in ("clear", "mostly clear"):
        return "sun"
    if "partly" in s:
        return "partly"
    return "cloud"


def _minutes(t):
    m = re.match(r"(\d+):(\d+)\s*(am|pm)", t or "")
    if not m:
        return None
    hh, mm = int(m.group(1)) % 12, int(m.group(2))
    return (hh + (12 if m.group(3) == "pm" else 0)) * 60 + mm


def daylight(rise, sets):
    a, b = _minutes(rise), _minutes(sets)
    if a is None or b is None or b <= a:
        return None
    return f"{(b - a) // 60} h {(b - a) % 60:02d} m"


_SNAP_RE = re.compile(r'<svg\b[^>]*>|</svg>|stroke-width(=")([0-9.]+)"|stroke-width(:)([0-9.]+)')


def _snap_strokes(doc):
    """Kindle Paperwhite pass: every engraved line lands on the device pixel grid. A stroke's on-screen width
    (stroke-width x the drawing's viewBox scale) is rounded up to a whole multiple of 0.5 CSS px, at least 0.5."""
    try:
        stack = [1.0]

        def sub(m):
            t = m.group(0)
            if t.startswith("<svg"):
                sc = stack[-1]
                vb = re.search(r'viewBox="\s*[-0-9.]+[ ,]+[-0-9.]+[ ,]+([0-9.]+)', t)
                wd = re.search(r'\swidth="([0-9.]+)(?:px)?"', t)
                if vb and wd and float(vb.group(1)) > 0:
                    sc = float(wd.group(1)) / float(vb.group(1))
                elif vb:
                    hs = re.search(r'height:\s*([0-9.]+)px', t)
                    vh = re.search(r'viewBox="\s*[-0-9.]+[ ,]+[-0-9.]+[ ,]+[0-9.]+[ ,]+([0-9.]+)', t)
                    if hs and vh and float(vh.group(1)) > 0:
                        sc = float(hs.group(1)) / float(vh.group(1))
                if not t.endswith("/>"):
                    stack.append(sc)
                return t
            if t == "</svg>":
                if len(stack) > 1:
                    stack.pop()
                return t
            v = float(m.group(2) or m.group(4))
            if v <= 0:
                return t
            sc = stack[-1] or 1.0
            px = max(.5, math.ceil(v * sc * 2 - 1e-6) / 2)
            nv = f"{px / sc:.3f}".rstrip("0").rstrip(".")
            return f'stroke-width="{nv}"' if m.group(1) else f"stroke-width:{nv}"

        return _SNAP_RE.sub(sub, doc)
    except Exception:  # noqa: BLE001
        return doc


_NREF = {}  # salt -> (medallions, vignettes) drawn in that page's filler defs


def _muse(salt, i, size, cls=""):
    """A medallion from this page's filler set (drawn once in its hidden defs), placed by reference."""
    return (f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" class="kmu{cls}" viewBox="0 0 100 100" width="{size}" height="{size}" aria-hidden="true">'
            f'<use xlink:href="#kmd{salt}{i % _NREF.get(salt, (4, 2))[0]}" width="100" height="100"/></svg>')


def _vuse(salt, i, h, cls=""):
    """A vignette from this page's filler set, by reference, h px tall."""
    return (f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" class="kvu{cls}" viewBox="0 0 120 80" width="{_n(h * 1.5)}" height="{h}" aria-hidden="true">'
            f'<use xlink:href="#kvg{salt}{i % _NREF.get(salt, (4, 2))[1]}" width="120" height="80"/></svg>')


def _dress(body, salt, close=False):
    """Fill a page's margins with engraving: medallions flank the head vignette, vignettes and medallions flank
    the tailpiece, and a framed plate (poem, close) gets medallion columns down its sides."""
    return body  # one plate per page now; the head, tail and asterism keep their single ornament
    try:
        tail = ORNAMENTS["tail"]
        if tail in body:
            t = 34
            row = (f'<div class="kflank kft">{_vuse(salt, 0, t)}{_muse(salt, 2, t)}{_muse(salt, 3, t)}{tail}'
                   f'{_muse(salt, 0, t)}{_muse(salt, 1, t)}{_vuse(salt, 1, t)}</div>')
            body = body[::-1].replace(tail[::-1], row[::-1], 1)[::-1]
        ast = ORNAMENTS["asterism"]
        if ast in body and engraving_thai:
            try:
                kb = engraving_thai.kranok_band(200, 14, sum(map(ord, salt)) + 7)
                l = kb.replace("<svg ", '<svg class="kastb" preserveAspectRatio="none" aria-hidden="true" ', 1)
                r = kb.replace("<svg ", '<svg class="kastb kastr" preserveAspectRatio="none" aria-hidden="true" ', 1)
                body = body.replace(ast, f'<div class="kflank kastrow">{l}{ast}{r}</div>', 1)
            except Exception:  # noqa: BLE001
                pass
        m = re.search(r'<div class="khv">', body)
        if m:
            e = body.index("</div>", m.end())
            n = 2 if "kplate" in body else 3
            body = (body[:m.start()] + '<div class="khv kflank">' + "".join(_muse(salt, i, 40) for i in range(n)) + body[m.end():e]
                    + "".join(_muse(salt, i + n, 40) for i in range(n)) + '</div>' + body[e + 6:])
        if "kplate kframe" in body or close:
            col = lambda off: "".join(_muse(salt, off + i, 46) for i in range(8))
            cols = f'<div class="kcol kcol-l">{col(0)}</div><div class="kcol kcol-r">{col(2)}</div>'
            body = body.replace(_corner_blocks(), _corner_blocks() + cols, 1) if not close else body
    except Exception:  # noqa: BLE001
        pass
    return body


def main(dash_path, ev_path, site):
    with open(dash_path) as f:
        d = json.load(f)
    ev = None
    if ev_path and os.path.exists(ev_path):
        try:
            with open(ev_path) as f:
                ev = json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_evening: ignoring {ev_path} ({e!r})")
    now = dt.datetime.now(dt.timezone.utc)
    if os.environ.get("EVENING_NOW"):  # for previews: build as if at this local time
        now = dt.datetime.fromisoformat(os.environ["EVENING_NOW"]).replace(tzinfo=TZ).astimezone(dt.timezone.utc)
    local = now.astimezone(TZ)
    night = evening.evening_of(local)
    out = os.path.join(site, "evening")
    os.makedirs(out, exist_ok=True)
    font_css, font_links = self_host_fonts(out)
    with open(os.path.join(out, "kindle.css"), "w") as f:
        try:
            art_css = _at.page_css(out, 3)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_evening: frame art skipped ({e!r})")
            art_css = ""
        f.write(font_css + "\n" + EINK_CSS + "\n" + EVENING_CSS + art_css)
    _ART["dir"] = out

    big, loc, by_model = stories(d, ev, night, now)
    for st in big + ([loc] if loc else []):
        st["headline"], st["next"] = smart(st["headline"]), smart(st.get("next"))
        st["paras"] = [smart(x) for x in st["paras"]]
    wx = evening.tomorrow(d, local)
    sky = evening.tonight(d, local)
    morning_poem = (d.get("poem") or {}).get("title")
    poem = bedtime_poems.tonight(night, morning_poem)
    weekday = night.strftime("%A")
    tmr = night + dt.timedelta(days=1)

    # ---- the pages, in reading order: (file, title, part, kicker, body)
    o = d.get("outside") or {}
    datef = f"{night:%A, %B} {night.day}"
    pages = []
    for k, st in enumerate(big, 1):
        pages.append({"file": f"day-{k}.html", "title": st["headline"], "part": "The day", "kick": "",
                      "run": "The day", "story": st, "head": "",
                      "band": datef, "nav": f"Story {k}"})
    # no news: the cover says so; a page that only repeats it would cost a page turn for nothing
    if loc:
        pages.append({"file": "local.html", "title": loc["headline"], "part": "Close to home", "kick": "",
                      "run": "Close to home", "story": loc, "head": "",
                      "band": "Close to Home &middot; Portland", "nav": "Portland"})
    over = '<p class="kover khr">Anything that changes overnight will be in your Morning Edition.</p>'
    if big or loc:
        pages[-1]["over"] = True

    def table(rows, cls=""):
        return (f'<table class="kt {cls}">' + "".join(f'<tr{" class=" + chr(34) + r[2] + chr(34) if len(r) > 2 else ""}><th>{r[0]}</th><td>{r[1]}</td></tr>' for r in rows if r[1]) + "</table>")

    days = {x.get("date"): x for x in o.get("days") or []}
    f_tm, f_td = days.get(tmr.isoformat()), days.get(night.isoformat())
    tmr_short = f"{tmr:%a, %b} {tmr.day}"

    def dur(mins):
        return f"{int(mins) // 60} h {int(mins) % 60} m"

    def sun_rows():
        """SUN and DAYLIGHT rows for tomorrow, from the forecast day (never invented)."""
        rows = []
        if f_tm and f_tm.get("sunrise") and f_tm.get("sunset"):
            rows.append(("Sun", f'Rises {evening.hhmm(f_tm["sunrise"])} &middot; sets {evening.hhmm(f_tm["sunset"])}'))
        if f_tm and f_tm.get("daylight_min"):
            v = dur(f_tm["daylight_min"])
            if f_td and f_td.get("daylight_min"):
                diff = round(f_tm["daylight_min"] - f_td["daylight_min"])
                v += (f", {abs(diff)} min {'less' if diff < 0 else 'more'} than today" if diff else ", the same as today")
            rows.append(("Daylight", v, "kdrop1"))
        return rows

    # Tomorrow: the answer first (labelled high and low, one-line verdict), then hour by hour, then the details
    if wx:
        alert = ""
        if wx["alerts"]:
            alert = (f'<div class="kp"><p class="klb">Alert</p><p class="kalert">{E(smart(wx["alerts"][0]))}</p>'
                     '<p class="knote">National Weather Service. Details in the morning.</p></div>')
        cmp_ = ""
        if f_td and f_td.get("hi") is not None:
            dd = wx["hi"] - round(f_td["hi"])
            cmp_ = ("about the same as today" if abs(dd) <= 1 else f"{abs(dd)}&deg; {'cooler' if dd < 0 else 'warmer'} than today")
        answer = (f'<div class="kp"><table class="kt kans"><tr><td class="khi"><p class="klb">High</p><span class="khero">{wx["hi"]}&deg;</span></td>'
                  f'<td><p class="klb">Low</p><span class="khero2">{wx["lo"]}&deg;</span>' + (f'<p class="knote">{cmp_}</p>' if cmp_ else "") + '</td></tr></table>'
                  f'<p class="klede2 khr">{E(smart(wx["lead"]))}</p></div>')
        hours = {h["t"]: h for dd, h in evening._dated_hours(d, local) if dd == tmr}
        cols = [hours[t] for t in ("07:00", "10:00", "13:00", "16:00", "19:00") if t in hours and hours[t].get("temp") is not None]
        hourly = ""
        if len(cols) >= 2:
            def skyw(c):
                return "" if c is None else "clear" if c < 40 else "some sun" if c < 85 else "cloudy"
            def rainc(h):
                r = h.get("rain_pct")
                return "" if r is None else (f"<b>{round(r)}%</b>" if r >= 50 else f"{round(r)}%")
            hourly = ('<div class="kp"><p class="klb">Hour by hour</p><table class="kt khours">'
                      '<tr><th></th>' + "".join(f'<th class="kc">{evening.hhmm(h["t"])}</th>' for h in cols) + '</tr>'
                      '<tr class="ktemp"><th>Temp</th>' + "".join(f'<td>{round(h["temp"])}&deg;</td>' for h in cols) + '</tr>'
                      + ('<tr><th>Rain</th>' + "".join(f'<td>{rainc(h)}</td>' for h in cols) + '</tr>' if any(h.get("rain_pct") is not None for h in cols) else "")
                      + ('<tr class="ksk kdrop2"><th>Sky</th>' + "".join(f'<td>{skyw(h.get("cloud"))}</td>' for h in cols) + '</tr>' if any(h.get("cloud") is not None for h in cols) else "")
                      + '</table></div>')
        rows = []
        if wx.get("rain_pct") is not None:
            rain = f'{round(wx["rain_pct"])}% chance'
            if wx["amount"] or wx["timing"]:
                rain += ". " + " ".join(E(smart(x)) for x in (wx["amount"], wx["timing"]) if x)
            elif (wx.get("rain_in") or 0) < 0.01:
                rain += ", none expected"
            rows.append(("Rain", rain))
        if f_tm and f_tm.get("wind") is not None:
            wind = f'{round(f_tm["wind"])} mph' + (f', gusts to {round(f_tm["gust"])}' if f_tm.get("gust") else "")
            rows.append(("Wind", wind + (". " + E(smart(wx["wind"].split(" Frost")[0])) if wx["wind"] and not wx["wind"].startswith("Frost") else "")))
        wear = ("Heavy coat; scrape the windshield" if wx["lo"] <= 33 else "Warm coat" if wx["hi"] < 50 else "Jacket or fleece" if wx["hi"] < 62
                else "A light layer" if wx["hi"] < 72 else "Short sleeves")
        rows.append(("Wear", wear + (", and a hood" if (wx.get("rain_pct") or 0) >= 40 else "")))
        if wx.get("frost"):
            rows.append(("Frost", E(smart(wx["frost"]))))
        rows += sun_rows()
        if f_tm and (f_tm.get("uv") or 0) >= 3:
            rows.append(("UV", f'{f_tm["uv"]:.0f}', "kdrop1"))
        body = (alert + answer + hourly + '<div class="kp">' + table(rows)
                + f'<p class="klede khr">{E(smart(wx["plan"]))}</p></div>')
    else:
        rows = sun_rows()
        mp = moon_phase(night)
        if mp:
            rows.append(("Moon", f"{E(mp[2])}, {mp[0]}% lit"))
        body = (f'<div class="kp"><p class="klb">Tomorrow &middot; {tmr_short}</p>'
                '<p class="klede2">The forecast didn&rsquo;t come through tonight. It will be in your Morning Edition.</p></div>'
                + (f'<div class="kp">{table(rows)}</div>' if rows else ""))
    pages.append({"file": "tomorrow.html", "title": "Tomorrow’s weather", "part": "Tomorrow", "nav": "Tomorrow",
                  "kick": f"Tomorrow &middot; {tmr:%A, %B} {tmr.day}", "body": body})

    # Tonight's sky: the verdict first (and the rare event), then where to look as a table, then the chart
    lat, lon = o.get("lat") or 45.7, o.get("lon") or -122.8
    try:
        mo = evening.moon(night, lat, lon)
        pl = [p for p in evening.planets(night, lat, lon) if p["mag"] <= 1.5][:3]
    except Exception as e:  # noqa: BLE001 - the page still prints without the drawing
        print(f"kindle_evening: sky drawing skipped ({e!r})")
        mo, pl = None, []
    phase = moon_phase(night)
    if mo and phase:
        phase = (mo["lit"], mo["name"].startswith(("Waxing", "First")), mo["name"])
    clouded = sky["clouds"] == "Clouded out"
    try:
        dark = evening.dusk(night, lat, lon)[1]
        sky_lab = f"Tonight &middot; dark by {evening.clock(dark.timetz())}"
    except Exception:  # noqa: BLE001
        sky_lab = "Tonight"
    # the rare event leads when there is one
    rare = None
    if sky["choice"]:
        for e in o.get("sky_events") or []:
            if e.get("kind") == "meteors" and e.get("title"):
                try:
                    peak = evening._parse_utc(e["utc"]).astimezone(TZ)
                    if (peak - dt.timedelta(hours=12)).date() == night:
                        nm = e["title"].replace(" meteor shower peak", "")
                        rare = f"{nm[:-1] if nm.endswith('s') else nm} meteors peak tonight"
                except Exception:  # noqa: BLE001
                    pass
        if not rare and "northern lights" in sky["choice"]:
            rare = "A chance of northern lights tonight"
    sky_head = smart(rare or sky["headline"] or "A quiet sky tonight")
    lede = {"Clear and steady": "Clear and steady.", "Clear but twinkly": "Clear, but twinkly.", "Some gaps": "Some clear gaps.",
            "Clear": "Clear skies."}.get(sky["clouds"] or "")
    if clouded:
        lede = "Nothing to see from the island. " + (sky["later"] or "")
    elif sky["clouds"] is None:
        lede = "Cloud forecast unavailable; look out the window."
    elif lede is None:
        lede = E(sky["clouds"]) + "."
    if rare and sky["headline"] and not clouded:
        lede = f'{lede} {E(smart(sky["headline"]))}.'
    verdict = (f'<div class="kp"><p class="klb">{sky_lab}</p><h2>{E(sky_head)}</h2><p class="klede">{E(smart(lede.strip()))}</p></div>')
    moon_row = ""
    if phase:
        lit, waxing, name = phase
        mv = "New moon: the darkest sky of the month" if lit < 3 else f"{E(name)} &middot; {lit}% lit" + ("" if mo else ", not up this evening")
        moon_row = f'<div class="kp">{table([("Moon", mv)])}</div>'
    if clouded:
        nrows = []
        for n in (o.get("nights") or []):
            try:
                nd = dt.date.fromisoformat(n["night"])
            except Exception:  # noqa: BLE001
                continue
            if nd > night and n.get("verdict") and len(nrows) < 4:
                nrows.append((f"{nd:%a}", E(n["verdict"])))
        behind = "; ".join([f"{p['name']} is in the {p['dir']}" for p in pl[:2]] + (["the moon is up"] if mo else []))
        hid = ([("Moon", mv)] if phase else []) + ([("Hidden", E(behind[0].upper() + behind[1:]) + ".")] if behind else [])
        body = (verdict + (f'<div class="kp"><p class="klb">The next nights</p>{table(nrows)}</div>' if nrows else "")
                + (f'<div class="kp"><p class="klb">Behind the cloud</p>{table(hid)}</div>' if hid else ""))
    else:
        look = []   # (sort key, when, what, where, until)
        if mo:
            look.append((mo["hour"] * 60, evening.clock(dt.time(mo["hour"])), "Moon",
                         f'{evening.height(mo["alt"]).capitalize()} in the {mo["dir"]}, {evening._lit_words(mo["lit"])}',
                         evening._when_sets(mo["sets"], night)))
        for p in pl:
            look.append((p["look"].hour * 60 + p["look"].minute + (0 if p["look"].hour >= 12 else 1440), evening.clock(p["look"].timetz()), p["name"],
                         f'{evening.height(p["alt"]).capitalize()} in the {p["dir"]}, {evening.LOOKS.get(p["name"], "")}'.rstrip(", "),
                         evening._when_sets(p["sets"], night)))
        look.sort(key=lambda r: r[0])
        for k, v in sky["items"]:
            if k == "Space station":
                when, _, rest = v.partition(", ")
                look.append((0, when, k, rest.split(". ")[0].rstrip(".").capitalize(), ""))
            elif k == "Meteors":
                look.append((0, "", k, v.rstrip("."), ""))
        look = look[:5]
        looks = ""
        if look:
            looks = ('<div class="kp"><table class="kt klook"><tr><th class="kw1">When</th><th class="kw2">What</th><th>Where</th><th class="kw4">Until</th></tr>'
                     + "".join(f"<tr><td>{E(w_)}</td><td><b>{E(n_)}</b></td><td>{E(smart(wh))}</td><td>{E(u)}</td></tr>" for _, w_, n_, wh, u in look)
                     + "</table></div>")
        chart = ""
        if mo or pl:
            chart = (f'<div class="koptw"><div class="kchart kopt">{sky_chart(pl, mo, phase, night)}<p class="kcap">Facing south. Positions at 9 pm unless marked.</p></div></div>')
        body = (verdict + (f'<div class="kp"><p class="klede">{E(smart(sky["choice"]))}</p></div>' if sky["choice"] else "")
                + looks + ("" if mo else moon_row) + chart)
    pages.append({"file": "sky.html", "title": "Tonight’s sky", "part": "Tonight’s sky", "notail": True, "nav": "Tonight’s sky",
                  "kick": f"Tonight &middot; {datef}", "body": body})

    if poem:
        pages.append({"file": "poem.html", "title": f"A poem: {poem['title']}", "part": "Before bed", "kick": "", "band": "Before Bed &middot; A Poem",
                      "body": poem_html(poem), "notail": True, "nav": "Poem"})
    recap = ""
    if wx:
        recap = (f'<p class="krecap">Tomorrow: high {wx["hi"]}&deg;' + (f'. Sunrise {wx["sunrise"]}' if wx.get("sunrise") else "") + '.</p>')
    pages.append({"file": "goodnight.html", "title": "Goodnight", "part": "", "kick": "", "close": True, "notail": True, "band": datef, "nav": "Goodnight",
                  "body": '<div class="kframe"><div class="kend kendtxt"><p class="kkick">The Evening Edition</p>'
                          '<h2 class="kfname">That&rsquo;s the day.</h2>'
                          '<p class="kfsub">Everything else can wait until morning.</p>'
                          f'<p class="kquiet">Think of one good thing from today, then let it go.</p>{recap}</div></div>'})

    for pg in pages:
        st = pg.get("story")
        if st:
            nx = st.get("next")
            nx = nx.strip() if isinstance(nx, str) else ""
            if nx.rstrip(".").lower() == "no date is set yet":
                nx = ""
            nxt = f'<p class="klb">Next</p><p class="klede">{E(nx)}</p>' if nx else ""
            paras = [E(p) for p in st["paras"]]
            if paras:
                first = st["paras"][0]
                if first[:1].isalpha():
                    paras[0] = f'<p class="kdrp"><span class="kini">{E(first[:1])}</span>{E(first[1:])}</p>'
                else:
                    paras[0] = f'<p>{paras[0]}</p>'
                paras[1:] = [f"<p>{x}</p>" for x in paras[1:]]
            pg["body"] = (f'<h2 class="khed">{E(st["headline"])}</h2><div class="kbody">' + "".join(paras) + "</div>"
                          + f'<div class="kp">{nxt}<p class="ksources{" khr" if nxt else ""}">{outlets_line(st)}</p>'
                          + (over if pg.get("over") else "") + '</div>')
        if pg.get("over") and not st:
            pg["body"] += over
        band = pg.get("band") or pg["kick"] or (E(pg["part"]) if pg["part"] else "Goodnight")
        salt = pg["file"].split(".")[0].replace("-", "")
        top = _top(band, salt, night)
        fill = _filler(night, salt, budget=PAGE_BYTES - 30000 - len(top) - len(pg["body"]),
                       moon=(_cycle(phase) if phase else None))
        if pg.get("close") and pg["body"].endswith("</div>"):
            pg["body"] = pg["body"][:-6] + fill + "</div>"
        else:
            pg["body"] = f'<div class="kframe klite">{pg["body"]}{fill}</div>'
        pg["body"] = (ORNAMENTS["defs"] if "ke-" in pg["body"] else "") + pg["body"] + FILL_JS
        pg["top"] = top

    # ---- chrome shared with the Morning Edition
    total = len(pages)
    files = [pg["file"] for pg in pages]
    _TITLES.clear()
    _TITLES.update({pg["file"]: pg.get("nav") or pg["title"] for pg in pages})   # short fixed labels: they never truncate
    _TITLES["index.html"] = "Front"
    edition = local.strftime("%-I:%M %p").lower().replace(":00 ", " ")
    gen = d.get("generated_at")
    stamp = E(f"Edition of {edition}")
    BUILD["id"] = f"evening {night.isoformat()} {edition}"

    def first_of(part_names):
        return next((pg["file"] for pg in pages if pg["part"] in part_names), None)

    def navigator(cur):
        pg = next(p for p in pages if p["file"] == cur)
        top = ['<nav id="kjump"><div class="kjtop">']
        if pg["part"] in ("The day", "Close to home"):
            to = first_of(("Tomorrow",))
            if to:
                top.append(f'<a class="kjskip" href="{to}"><small>Skip the news</small>Tomorrow&rsquo;s weather &rsaquo;</a>')
        elif pg["part"] in ("Tomorrow", "Tonight’s sky"):
            to = first_of(("Before bed",))
            if to:
                top.append(f'<a class="kjskip" href="{to}"><small>Skip to</small>The poem &rsaquo;</a>')
        top.append('<a class="kjfront" href="index.html"><small>Back to</small>The front</a></div>')
        top.append('<p class="kjh">This evening</p><div class="kjg">')
        top += [f'<a href="{p["file"]}"{" class=\"kjcur\"" if p["file"] == cur else ""}><i>{n}</i>{E(p["title"])}</a>'
                for n, p in enumerate(pages, 1)]
        top.append("</div></nav>")
        return "".join(top)

    for n, pg in enumerate(pages):
        prev = files[n - 1] if n else "index.html"
        nxt = files[n + 1] if n + 1 < total else None
        label = _TITLES.get(nxt) if nxt else None
        doc = page(pg["title"], pg["body"], "kev", "kcard" if not pg.get("close") else "ksecfront kendpage",
                   prev=prev, nxt=nxt, stamp=stamp, run_left=pg.get("run") or (E(pg["part"]) if pg["part"] else "Goodnight"),
                   run_right=f"Page {n + 2} of {total + 1}", fonts=font_links, next_label=label, run_href="index.html",
                   jump=navigator(pg["file"]))
        doc = doc.replace("</nav>", "</nav>" + pg.get("top", ""), 1)  # the title plaque sits in the frame's top band, above the paged view
        if pg.get("close"):
            # The running head names the page; it isn't a link back.
            doc = doc.replace('<nav class="krun"><a href="index.html">Goodnight</a>', '<nav class="krun"><span class="krunh">Goodnight</span>', 1)
            # The last page: nothing after it, and a right tap stays put.
            doc = re.sub(r'<a class="knx"[^>]*>.*?</a>', '<span class="knx"></span>', doc)
            doc = re.sub(r'<a class="knext"[^>]*>.*?</a>', "", doc, flags=re.S)
            doc = doc.replace("else go(NEXT_URL); }", "else if (NEXT_URL) go(NEXT_URL); }")
        with open(os.path.join(out, pg["file"]), "w") as f:
            f.write(_snap_strokes(doc))

    # ---- the cover: nameplate, arms, then three labelled panels: tomorrow, the day, tonight
    words = sum(len(re.sub(r"<svg\b.*?</svg>|<script\b.*?</script>|<[^>]+>|&\w+;", " ", pg["body"], flags=re.S).split()) for pg in pages)
    minutes = math.ceil(words / 200) + 1
    day_pages = [pg for pg in pages if pg.get("story")]
    lead_lines = sum(min(2, math.ceil(len(pg["title"]) / 46)) for pg in day_pages)
    # tomorrow: the labelled high leads, the low under it, the verdict beside
    if wx:
        tm = ('<div class="kp">'
              + (f'<p class="kalert kal2"><span class="klb">Alert</span> {E(smart(wx["alerts"][0]))}</p>' if wx["alerts"] else "")
              + f'<table class="kt kcv"><tr><td class="khi"><p class="klb">High</p><span class="khero3">{wx["hi"]}&deg;</span>'
              f'<p class="klow">Low {wx["lo"]}&deg;</p></td><td class="kcl"><p class="klb">Tomorrow &middot; {tmr_short}</p>'
              f'<p class="klede">{E(smart(wx["lead"]))}</p></td></tr></table></div>')
        est = 119 + (32 if wx["alerts"] else 0) + max(0, math.ceil(len(wx["lead"]) / 34) - 3) * 26
    else:
        sr = sun_rows()[:1]
        tm = (f'<div class="kp"><p class="klb">Tomorrow &middot; {tmr_short}</p>'
              '<p class="klede">The forecast didn&rsquo;t come through tonight.</p>' + (table(sr, "khr") if sr else "") + '</div>')
        est = 16 + 26 + 30 + (38 if sr else 0)
    # one table of what is inside: the stories by number, Portland, the sky, the moon, the poem
    def lines(t):
        return math.ceil(len(t) / 43)
    rows_, k = [], 0
    for pg in day_pages:
        if pg["part"] == "The day":
            k += 1
        rows_.append(["story", str(k) if pg["part"] == "The day" else "Portland",
                      f'<a class="khl" href="{pg["file"]}">{E(pg["title"])}</a>', lines(pg["title"])])
    if not day_pages:
        rows_.append(["none", "The day", "Tonight&rsquo;s news didn&rsquo;t come through. It will be in your Morning Edition.", 2])
    rows_.append(["sky", "Sky", f'<a href="sky.html">{E(sky_head)}</a>', lines(sky_head)])
    if not wx and not day_pages and not clouded and look:
        _, w_, n_, wh, u = look[0]
        v = f"<b>{E(n_)}</b>" + (f" at {E(w_)}" if w_ else "") + f": {E(smart(wh[0].lower() + wh[1:]))}"
        rows_.append(["look", "Look", v, lines(re.sub(r"<[^>]+>", "", v))])
    if phase:
        rows_.append(["moon", "Moon", mv, lines(re.sub(r"&\w+;", "-", mv))])
    if poem:
        v = E(smart(poem["title"])) + (f', {E(poem["poet"])}' if poem.get("poet") else "")
        rows_.append(["poem", "Poem", f'<a href="poem.html">{v}</a>', lines(v)])
    # the arms keep at least their smallest plate; rows give way only when the page cannot hold them
    _DROP = {"moon": "kdrop1", "poem": "kdrop2", "look": "kdrop3"}
    inside = '<div class="kp">' + table([(r[1], r[2]) + ((_DROP[r[0]],) if r[0] in _DROP else ()) for r in rows_], "kinside") + '</div>'
    npg = total + 1
    cm = _cycle(phase) if phase else .5
    cv = []
    for ch in (112, 132, 156, 180):
        try:
            u = _art(f"arms-cover-{ch}.svg", lambda: _at.arms_panel(_at.PANEL_W, ch, _at._seed("arms"), flank=("river", "bridge"), moon=cm))
            cv.append(f'<div class="kca" data-h="{ch}" style="height:{ch}px;background:url({u}) 50% 50%/{_at.PANEL_W}px {ch}px no-repeat !important"></div>')
        except Exception:  # noqa: BLE001
            pass
    centre = f'<div class="kcentre" aria-hidden="true">{"".join(cv)}</div>' if cv else ""
    body = ('<div class="kframe kcover">' + _top("Private Edition &middot; Sauvie Island", "cover", night)
            + f'<div class="kmast"><p class="kname">The Evening Edition</p>'
            f'<p class="kdate"><span class="kdl">{night:%A, %B} {night.day}</span><span class="kdr">{E(edition)} &middot; {minutes}-minute read</span></p></div>'
            + centre + tm + inside
            + _filler(night, "cover", budget=90000, moon=(_cycle(phase) if phase else None)) + '</div>' + FILL_JS)
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(_snap_strokes(page("The Evening Edition", body, "kev", "kcontents", nxt=files[0], stamp=stamp, run_left="",
                     run_right=f"Page 1 of {npg}", fonts=font_links,
                     next_label=("Begin: the day" if day_pages else _TITLES[files[0]]))))
    with open(os.path.join(site, "evening.html"), "w") as f:
        f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=evening/index.html">'
                '<a href="evening/index.html">Open the Evening Edition</a>')
    _JUMP[0] = ""
    print(f"kindle_evening: {total} pages for the evening of {night} "
          f"({'local model summaries' if by_model else 'feed summaries'}; data from {gen})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else "_site")
