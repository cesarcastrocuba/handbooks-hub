-- Convert Pandoc's unchecked-task marker to a readable empty square.
-- This is content-safe: only the marker glyph changes, not list semantics.
function Str(el)
  if el.text == "☐" then
    el.text = "□"
  end
  return el
end
