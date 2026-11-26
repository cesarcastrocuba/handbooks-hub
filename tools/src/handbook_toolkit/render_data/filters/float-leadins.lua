-- Keep a heading and one short introduction with the next table or figure.
-- A figure stays right after the text that introduces it, as in the Word edition
-- (Owner decision 2026-11-23): handbook-figure-group keeps it with its lead-in and
-- only scales it when it nearly fits the gap in front of it. Tables keep the
-- measured handbook-float-group.
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

-- An image float; a Figure or Div that holds a table stays a table float.
local function figure(block)
  if block.t == "Para" then
    return #block.content == 1 and block.content[1].t == "Image"
  end
  if block.t ~= "Figure" and not (block.t == "Div" and block.identifier:match("^fig%-")) then
    return false
  end
  local table = false
  block:walk({ Table = function() table = true end })
  return not table
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
      local group = figure(block) and "handbook-figure-group" or "handbook-float-group"
      if #lead > 0 or figure(block) then
        -- Flat raw blocks, not a Div: a Div renders as a breakable #block[ and
        -- Typst shrinks an image to that block's remaining space.
        -- A figure group opens its images from the document, where their paths resolve.
        local open = figure(block) and 'open: p => image(p, alt: "handbook-natural"), ' or ""
        result:insert(pandoc.RawBlock("typst", "#" .. group .. "(" .. open .. "lead: ["))
        result:extend(lead)
        result:insert(pandoc.RawBlock("typst", "], body: ["))
        result:insert(block)
        result:insert(pandoc.RawBlock("typst", "])"))
      else result:insert(block) end
    else result:insert(block) end
  end
  return result
end
