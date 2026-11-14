-- The first canonical page is staged as index.qmd. Rebase its relative images once,
-- before any writer consumes them, rather than repairing each rendered format.
local base = ""
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

return {{Meta = function(meta)
  base = pandoc.utils.stringify(meta["handbook-index-source-dir"] or "")
end}, {Image = rebase_image}}
