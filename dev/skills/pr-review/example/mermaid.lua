-- Draw ```mermaid blocks as diagrams (drawn in the browser by mermaid.html),
-- and point ../ links to the code on GitHub (code-base-url in _quarto.yml).

local base

local function escape(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

return {
  {
    Meta = function(m)
      if m["code-base-url"] then
        base = pandoc.utils.stringify(m["code-base-url"])
      end
    end,
  },
  {
    CodeBlock = function(el)
      if el.classes[1] == "mermaid" then
        return pandoc.RawBlock("html", '<pre class="mermaid">' .. escape(el.text) .. "</pre>")
      end
    end,
    Link = function(el)
      -- ../ or ../../ (files in block folders): strip to a repo-root path
      if base and el.target:match("^%.%./") then
        el.target = base .. el.target:gsub("^[%./]+", "")
        el.attributes["target"] = "_blank"
        return el
      end
    end,
  },
}
