require 'cgi'

source, output = ARGV
lines = File.readlines(source, chomp: true)

def inline(text)
  value = CGI.escapeHTML(text)
  value.gsub!(/`([^`]+)`/, '<code>\1</code>')
  value.gsub!(/\*\*([^*]+)\*\*/, '<strong>\1</strong>')
  value.gsub!(/\[([^\]]+)\]\(([^)]+)\)/, '<a href="\2">\1</a>')
  value.gsub!(/&lt;(https?:\/\/[^&]+)&gt;/, '<a href="\1">\1</a>')
  value.gsub!(/&lt;br&gt;/, '<br>')
  value
end

body = []
index = lines.index { |line| line.start_with?('## 1. ') } || 0
i = index
list = nil

while i < lines.length
  line = lines[i]
  if line.start_with?('```')
    body << "</#{list}>" if list
    list = nil
    language = line.delete_prefix('```')
    code = []
    i += 1
    while i < lines.length && !lines[i].start_with?('```')
      code << lines[i]
      i += 1
    end
    body << "<pre data-language=\"#{CGI.escapeHTML(language)}\"><code>#{CGI.escapeHTML(code.join("\n"))}</code></pre>"
  elsif line.match?(/^\#{2,4} /)
    body << "</#{list}>" if list
    list = nil
    level = line[/^#+/].length
    body << "<h#{level}>#{inline(line.sub(/^#+\s+/, ''))}</h#{level}>"
  elsif line.start_with?('|') && i + 1 < lines.length && lines[i + 1].match?(/^\|[\s|:-]+\|$/)
    body << "</#{list}>" if list
    list = nil
    rows = []
    while i < lines.length && lines[i].start_with?('|')
      rows << lines[i].split('|')[1..-1].map(&:strip)
      i += 1
    end
    i -= 1
    rows.delete_at(1)
    header = rows.shift
    body << '<table><thead><tr>' + header.map { |cell| "<th>#{inline(cell)}</th>" }.join + '</tr></thead><tbody>'
    rows.each { |row| body << '<tr>' + row.map { |cell| "<td>#{inline(cell)}</td>" }.join + '</tr>' }
    body << '</tbody></table>'
  elsif line.match?(/^- /)
    if list != 'ul'
      body << "</#{list}>" if list
      body << '<ul>'
      list = 'ul'
    end
    body << "<li>#{inline(line.sub(/^- /, ''))}</li>"
  elsif line.match?(/^\d+\. /)
    if list != 'ol'
      body << "</#{list}>" if list
      body << '<ol>'
      list = 'ol'
    end
    body << "<li>#{inline(line.sub(/^\d+\. /, ''))}</li>"
  elsif line.empty?
    body << "</#{list}>" if list
    list = nil
  else
    body << "</#{list}>" if list
    list = nil
    paragraph = [line]
    while i + 1 < lines.length && !lines[i + 1].empty? &&
          !lines[i + 1].match?(/^(\#{2,4} |```|\|.*\||- |\d+\. )/)
      i += 1
      paragraph << lines[i]
    end
    body << "<p>#{inline(paragraph.join(' '))}</p>"
  end
  i += 1
end
body << "</#{list}>" if list

html = <<~HTML
  <!doctype html>
  <html lang="fr"><head><meta charset="utf-8"><title>Documentation technique - Projet Réservations</title>
  <style>
  @page { size: A4; margin: 17mm 16mm 18mm; }
  * { box-sizing: border-box; }
  html, body { background: #fff !important; color-scheme: light; }
  body { margin: 0; color: #222; font: 9.4pt/1.32 Arial, sans-serif; }
  .cover { height: 258mm; page-break-after: always; position: relative; text-align: center; border-top: 8px solid #781f3c; }
  .icc { position: absolute; top: 18mm; left: 0; width: 35mm; color: #781f3c; text-align: left; }
  .icc b { display: block; font: 28pt Georgia, serif; letter-spacing: 2px; }
  .icc span { font-size: 7.5pt; line-height: 1.2; display: block; }
  .cover-main { padding-top: 82mm; }
  .cover h1 { color: #781f3c; font: bold 25pt/1.15 Georgia, serif; margin: 0 0 8mm; }
  .cover h2 { font: normal 15pt Arial, sans-serif; margin: 0; color: #333; }
  .cover-meta { position: absolute; bottom: 20mm; width: 100%; border-top: 1px solid #c9a9b5; padding-top: 7mm; }
  .cover-meta p { margin: 2mm 0; }
  h2 { color: #781f3c; font-size: 15pt; margin: 7mm 0 2.5mm; border-bottom: 1px solid #c9a9b5; padding-bottom: 1.5mm; break-after: avoid; }
  h3 { color: #5f1830; font-size: 11.5pt; margin: 5mm 0 1.5mm; break-after: avoid; }
  h4 { color: #333; font-size: 10pt; margin: 4mm 0 1mm; break-after: avoid; }
  p { margin: 0 0 2.4mm; text-align: left; }
  ul, ol { margin: 1mm 0 3mm 6mm; padding-left: 4mm; }
  li { margin: 0 0 1mm; }
  table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; font-size: 8.5pt; break-inside: avoid; }
  th { background: #781f3c; color: white; text-align: left; }
  th, td { border: 1px solid #c9a9b5; padding: 1.6mm 2mm; vertical-align: top; }
  tr:nth-child(even) td { background: #f7f1f3; }
  code { font: 8.3pt Menlo, monospace; background: #f3f3f3; padding: 0 .5mm; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f3f3f3; border-left: 3px solid #781f3c; padding: 2.5mm; margin: 2mm 0 4mm; break-inside: avoid; }
  pre code { padding: 0; }
  a { color: #5f1830; text-decoration: none; }
  </style></head><body>
  <section class="cover">
    <div class="icc"><b>ICC</b><span>Institut des Carrières Commerciales<br>Ville de Bruxelles</span></div>
    <div class="cover-main"><h1>Documentation technique</h1><h2>Projet Réservations</h2></div>
    <div class="cover-meta"><p><strong>Projet d'intégration et de développement</strong></p><p>Lisa Veaceslav</p><p>Année académique 2025-2026</p><p>Dernière mise à jour : 31 août 2026</p></div>
  </section>
  #{body.join("\n")}
  </body></html>
HTML

File.write(output, html)
