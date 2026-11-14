-- A book whose own first page is the root index.qmd keeps that page under a web-only name,
-- because the reading site's cover takes index.qmd. Links to it follow the new name.
-- Images need no filter: the toolkit rebases the staged first page's images before rendering.
local source_alias = ""

local function rebase_link(link)
  if not FORMAT:match("html") or source_alias == "" then return nil end
  local path, fragment = link.target:match("^([^#]*)(.*)$")
  if path == "" or path:match("^%a[%w+.-]*:") or path:sub(1, 1) == "/" then return nil end
  local directory = pandoc.path.directory(quarto.doc.input_file)
  local resolved = pandoc.path.normalize(pandoc.path.join({directory, path}))
  local relative = pandoc.path.make_relative(resolved, quarto.project.directory)
  if relative == "index.qmd" then
    link.target = pandoc.path.make_relative(pandoc.path.join({quarto.project.directory, source_alias}), directory) .. fragment
    return link
  end
end

return {{Meta = function(meta)
  source_alias = pandoc.utils.stringify(meta["handbook-root-source-index"] or "")
end}, {Link = rebase_link}}
