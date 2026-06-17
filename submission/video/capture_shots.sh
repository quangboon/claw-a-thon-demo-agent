#!/usr/bin/env bash
# Chụp ảnh thật từng bước demo trên site live (để dựng slideshow video).
set -u
BASE="https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn"
DIR="/Users/lap17708/develop_quang/claw-a-thon-demo-agent/submission/video/shots"
AB="agent-browser"
mkdir -p "$DIR"

ev(){ $AB eval "$1" >/dev/null 2>&1; }
shot(){ $AB screenshot "$DIR/$1" >/dev/null 2>&1; echo "  shot $1"; }
clickText(){ ev "(function(){var t='$1';var el=[...document.querySelectorAll('button,a')].find(e=>e.textContent.replace(/\s+/g,' ').trim().includes(t));if(el)el.click();return !!el})()"; }
fillInput(){ ev "(function(){var el=[...document.querySelectorAll('input')][$1];if(!el)return;var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(el,'$2');el.dispatchEvent(new Event('input',{bubbles:true}))})()"; }
fillTextarea(){ ev "(function(){var el=document.querySelector('textarea');if(!el)return;var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;s.call(el,'$1');el.dispatchEvent(new Event('input',{bubbles:true}))})()"; }
selectByText(){ ev "(function(){var s=[...document.querySelectorAll('select')][$1];if(!s)return;var o=[...s.options].find(o=>o.text.includes('$2'));if(!o)return;var set=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;set.call(s,o.value);s.dispatchEvent(new Event('change',{bubbles:true}))})()"; }

echo ">> setup"
$AB viewport 1366 768 >/dev/null 2>&1
$AB open "$BASE/?cb=$(date +%s)" >/dev/null 2>&1; sleep 3
ev "localStorage.removeItem('authToken');localStorage.setItem('activeProfileId','default');void 0"
$AB open "$BASE/?cb=$(date +%s)" >/dev/null 2>&1; sleep 3

echo ">> scene 1: login"
fillInput 0 "admin"; fillInput 1 "ClawAThon@2026"; sleep 1
shot 01_login.png
clickText "Đăng nhập"; sleep 4
shot 02_playground_empty.png

echo ">> scene 2: playground translate (default vi)"
selectByText 0 "Default"; sleep 1
fillTextarea "灵石 +20%，开放传送阵。完成每日任务可领取仙缘礼包，突破境界获得额外修为。"; sleep 1
shot 03_pg_source.png
clickText "Dịch + QC"; sleep 7
shot 04_pg_result.png

echo ">> scene 3: termbase"
clickText "Termbase"; sleep 3
fillInput 0 "灵"; sleep 2
shot 05_termbase.png
clickText "Đề xuất"; sleep 3
shot 06_candidates.png

echo ">> scene 4: human-in-the-loop"
clickText "Playground"; sleep 2
selectByText 0 "Game B"; sleep 2
selectByText 2 "ภาษาไทย"; sleep 1
fillTextarea "完成每日任务可领取礼包。"; sleep 1
clickText "Dịch + QC"; sleep 7
shot 07_pg_review_needed.png
clickText "Review Queue"; sleep 3
shot 08_review_queue.png
clickText "Sửa lại"; sleep 1
fillTextarea "ทำภารกิจประจำวันเพื่อรับของรางวัล"; sleep 1
shot 09_review_edit.png
clickText "Lưu sửa"; sleep 2

echo ">> scene 5: corrections"
clickText "Corrections"; sleep 3
shot 10_corrections.png

echo ">> scene 6: dashboard"
clickText "Dashboard"; sleep 3
shot 11_dashboard.png

echo ">> done"; ls -la "$DIR"
