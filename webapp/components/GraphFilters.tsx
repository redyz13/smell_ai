import { ChangeEvent, Dispatch, SetStateAction } from "react";

export type FilterState = {
  showSmelly: boolean;
  showCallingSmelly: boolean;
  showClean: boolean;
};

type GraphFiltersProps = {
  filters: FilterState;
  setFilters: Dispatch<SetStateAction<FilterState>>;
};

export default function GraphFilters({ filters, setFilters }: GraphFiltersProps) {
  const handleCheckboxChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFilters((prev) => ({ ...prev, [name]: checked }));
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow-md border border-gray-200 mb-4 flex flex-wrap gap-6 items-center">
      <h3 className="font-semibold text-gray-700">Filtri Grafo:</h3>
      
      <label className="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity">
        <input
          type="checkbox"
          name="showSmelly"
          checked={filters.showSmelly}
          onChange={handleCheckboxChange}
          className="w-4 h-4 text-red-600 rounded focus:ring-red-500"
        />
        <span className="text-sm font-medium text-gray-700">
          Mostra nodi smelly <span className="text-red-500">(Rosso)</span>
        </span>
      </label>

      <label className="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity">
        <input
          type="checkbox"
          name="showCallingSmelly"
          checked={filters.showCallingSmelly}
          onChange={handleCheckboxChange}
          className="w-4 h-4 text-orange-500 rounded focus:ring-orange-400"
        />
        <span className="text-sm font-medium text-gray-700">
          Mostra chiamanti smelly <span className="text-orange-500">(Arancione)</span>
        </span>
      </label>

      <label className="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity">
        <input
          type="checkbox"
          name="showClean"
          checked={filters.showClean}
          onChange={handleCheckboxChange}
          className="w-4 h-4 text-green-500 rounded focus:ring-green-400"
        />
        <span className="text-sm font-medium text-gray-700">
          Mostra nodi clean <span className="text-green-500">(Verde)</span>
        </span>
      </label>
    </div>
  );
}