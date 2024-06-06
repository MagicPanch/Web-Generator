import { SECTIONS } from "../constants/sections";

const componentMap = SECTIONS.reduce((map, section) => {
  map[section.name] = require(`../components/${section.component}`).default;
  return map;
}, {} as Record<string, React.ComponentType>);

export default componentMap;