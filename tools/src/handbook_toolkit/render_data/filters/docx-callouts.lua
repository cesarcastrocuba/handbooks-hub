-- Give Quarto callouts a Word paragraph style with a coloured title, a left rule and a tinted
-- background. The styles are defined in the generated reference.docx. Other formats keep the
-- original callout Div untouched.
local kinds = {
  ["callout-note"] = "Note",
  ["callout-tip"] = "Tip",
  ["callout-warning"] = "Warning",
  ["callout-important"] = "Important",
}

function Div(el)
  if FORMAT ~= "docx" then
    return nil
  end
  local name = nil
  for _, class in ipairs(el.classes) do
    if kinds[class] then
      name = kinds[class]
    end
  end
  if name == nil then
    return nil
  end
  local title_text = el.attributes["title"] or name
  local title = pandoc.Div(
    { pandoc.Para({ pandoc.Str(title_text) }) },
    pandoc.Attr("", {}, { ["custom-style"] = "Callout" .. name .. "Title" })
  )
  local body = pandoc.Div(
    el.content,
    pandoc.Attr("", {}, { ["custom-style"] = "Callout" .. name .. "Body" })
  )
  local end_marker = pandoc.Div(
    { pandoc.Para({ pandoc.Str(" ") }) },
    pandoc.Attr("", {}, { ["custom-style"] = "CalloutEnd" })
  )
  return pandoc.Div({ title, body, end_marker })
end
