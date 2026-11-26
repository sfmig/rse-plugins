-- Turn GitHub alerts (> [!NOTE], > [!TIP], ...) into Quarto callouts,
-- so the .md files render as callouts both on GitHub and in Quarto.
-- Text after the marker on the same paragraph becomes the callout title.

local types = {
  NOTE = "note",
  TIP = "tip",
  IMPORTANT = "important",
  WARNING = "warning",
  CAUTION = "caution",
}

function BlockQuote(el)
  local first = el.content[1]
  if not first or first.t ~= "Para" or #first.content == 0 then
    return nil
  end
  local marker = first.content[1]
  if marker.t ~= "Str" then
    return nil
  end
  local kind = marker.text:match("^%[!(%u+)%]$")
  local ctype = kind and types[kind]
  if not ctype then
    return nil
  end

  -- Remaining inlines of the first paragraph (minus leading spaces) = title
  local rest = pandoc.List()
  for i = 2, #first.content do
    rest:insert(first.content[i])
  end
  while #rest > 0 and (rest[1].t == "Space" or rest[1].t == "SoftBreak") do
    rest:remove(1)
  end

  local body = pandoc.List()
  for i = 2, #el.content do
    body:insert(el.content[i])
  end

  return quarto.Callout({
    type = ctype,
    title = #rest > 0 and pandoc.Inlines(rest) or nil,
    content = pandoc.Blocks(body),
  })
end
