-- Keep a heading and one short introduction with the next table/figure.
-- Native AST nodes remain intact for Quarto's numbering, links and other writers.
local utf8 = require("utf8")

local function float(block)
  if block.t == "Table" or block.t == "Figure" then return true end
  if block.t == "Para" then
    return #block.content == 1 and block.content[1].t == "Image"
  end
  return block.t == "Div" and (block.identifier:match("^fig%-") ~= nil or block.identifier:match("^tbl%-") ~= nil)
end

local function short(block)
  if block.t ~= "Para" or float(block) then return false end
  local text = pandoc.utils.stringify(block)
  local words = 0
  for _ in text:gmatch("%S+") do words = words + 1 end
  return words > 0 and words <= 80 and (utf8.len(text) or #text) <= 600
end

function Blocks(blocks)
  if FORMAT ~= "typst" then return nil end
  local result = pandoc.List()
  for _, block in ipairs(blocks) do
    if float(block) then
      local lead = pandoc.List()
      if #result > 0 and short(result[#result]) then
        lead:insert(1, result:remove(#result))
      end
      while #result > 0 and result[#result].t == "Header" and result[#result].level > 1 do
        lead:insert(1, result:remove(#result))
      end
      if #lead > 0 then
        local group = pandoc.List({pandoc.RawBlock("typst", "#handbook-float-group(lead: [")})
        group:extend(lead)
        group:insert(pandoc.RawBlock("typst", "], body: ["))
        group:insert(block)
        group:insert(pandoc.RawBlock("typst", "])"))
        result:insert(pandoc.Div(group))
      else result:insert(block) end
    else result:insert(block) end
  end
  return result
end
