-- One row of tabs, coloured by section.
-- A div {.section-NAME} inside a .panel-tabset marks each top heading in it
-- with an empty span.tab-NAME (styled in styles.css), then is unwrapped so
-- its headings stay direct children of the tabset and become tabs.
-- Runs at pre-ast: Quarto builds the tabs before ordinary user filters run.
function Div(div)
  if not div.classes:includes("panel-tabset") then
    return nil
  end
  local out = pandoc.List()
  for _, block in ipairs(div.content) do
    local section = block.t == "Div"
      and #block.classes > 0
      and block.classes[1]:match("^section%-(.+)")
    if section then
      for _, b in ipairs(block.content) do
        if b.t == "Header" and b.level == 1 then
          b.content:insert(pandoc.Span({}, { class = "tab-" .. section }))
        end
        out:insert(b)
      end
    else
      out:insert(block)
    end
  end
  div.content = out
  return div
end
