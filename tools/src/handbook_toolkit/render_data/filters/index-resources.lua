-- The first canonical page is staged as index.qmd. Rebase its relative images once,
-- before any writer consumes them, rather than repairing each rendered format.
local base = ""
local source_alias = ""
local function rebase_image(image)
  local input = quarto.doc.input_file
  if pandoc.path.filename(input) ~= "index.qmd" or base == "" then
    return nil
  end
  if image.src:match("^%a[%w+.-]*:") or image.src:sub(1, 1) == "/" then
    return nil
  end
  image.src = pandoc.path.normalize(pandoc.path.join({base, image.src}))
  return image
end

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
  base = pandoc.utils.stringify(meta["handbook-index-source-dir"] or "")
  source_alias = pandoc.utils.stringify(meta["handbook-root-source-index"] or "")
end}, {Image = rebase_image, Link = rebase_link}}
