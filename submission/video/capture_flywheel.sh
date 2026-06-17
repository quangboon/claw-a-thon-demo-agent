#!/usr/bin/env bash
# Chụp cảnh flywheel (tiếng Việt, đọc được): correction "Tinh thần→Máy chủ" đã học,
# dịch lại đúng nội dung đó → output dịch ĐÚNG "Máy chủ" (không lặp lỗi cũ).
set -u
BASE="https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn"
DIR="/Users/lap17708/develop_quang/claw-a-thon-demo-agent/submission/video/shots"
AB="agent-browser"
ev(){ $AB eval "$1" >/dev/null 2>&1; }
shot(){ $AB screenshot "$DIR/$1" >/dev/null 2>&1; echo "  shot $1"; }
clickText(){ ev "(function(){var t='$1';var el=[...document.querySelectorAll('button,a')].find(e=>e.textContent.replace(/\s+/g,' ').trim().includes(t));if(el)el.click();return !!el})()"; }
fillInput(){ ev "(function(){var el=[...document.querySelectorAll('input')][$1];if(!el)return;var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(el,'$2');el.dispatchEvent(new Event('input',{bubbles:true}))})()"; }
fillTextarea(){ ev "(function(){var el=document.querySelector('textarea');if(!el)return;var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;s.call(el,'$1');el.dispatchEvent(new Event('input',{bubbles:true}))})()"; }
selectByText(){ ev "(function(){var s=[...document.querySelectorAll('select')][$1];if(!s)return;var o=[...s.options].find(o=>o.text.includes('$2'));if(!o)return;var set=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;set.call(s,o.value);s.dispatchEvent(new Event('change',{bubbles:true}))})()"; }

$AB viewport 1366 768 >/dev/null 2>&1
$AB open "$BASE/?cb=$(date +%s)" >/dev/null 2>&1; sleep 3
ev "localStorage.removeItem('authToken');localStorage.setItem('activeProfileId','game-a');void 0"
$AB open "$BASE/?cb=$(date +%s)" >/dev/null 2>&1; sleep 3
fillInput 0 "admin"; fillInput 1 "ClawAThon@2026"; sleep 1
clickText "Đăng nhập"; sleep 4

# ảnh 1: corrections game-a (cặp Tinh thần -> Máy chủ)
selectByText 0 "Game A"; sleep 1
clickText "Corrections"; sleep 3
shot 12_fly_corrections.png

# ảnh 2: dịch lại đúng nội dung đó -> output "Máy chủ"
clickText "Playground"; sleep 2
selectByText 0 "Game A"; sleep 1
selectByText 2 "Tiếng Việt"; sleep 1
fillTextarea "服务器将于今晚23点进行停机维护两小时。"; sleep 1
clickText "Dịch + QC"; sleep 7
shot 13_fly_result.png
$AB eval "(()=>{var m=document.querySelector('main');var t=m.innerText;var i=t.indexOf('dịch bởi AI');return t.slice(Math.max(0,i-90),i)})()" 2>&1 | tail -1
rm -f "$DIR/12_flywheel_result.png" 2>/dev/null
